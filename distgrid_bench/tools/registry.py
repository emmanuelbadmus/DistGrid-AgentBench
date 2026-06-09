from __future__ import annotations

import inspect
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from distgrid_bench.tools.bess_analysis import (
    BESSAnalyzer,
    BESSLoader,
    BESSOptimizer,
    BESSSimulator,
)
from distgrid_bench.tools.combined_td import CombinedTDTools
from distgrid_bench.tools.dsse_adapter import DSSEAdapter
from distgrid_bench.tools.gfi_analysis import GFIAnalyzer, GFILoader, GFIPlotter, GFISimulator
from distgrid_bench.tools.pv_analysis import PVAnalyzer, PVGeneration, PVLoader
from distgrid_bench.tools.shared_registry import SharedRegistry

try:
    from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
    from distgrid_bench.tools.network.network_loader import NetworkLoader
    from distgrid_bench.tools.network.network_simulator import NetworkSimulator
    _NETWORK_CLASSES: tuple = (NetworkLoader, NetworkAnalyzer, NetworkSimulator)
except ImportError:
    _NETWORK_CLASSES = ()


ToolCallable = Callable[..., Any]


PUBLIC_TOOL_CLASSES = (
    BESSLoader,
    BESSAnalyzer,
    BESSSimulator,
    BESSOptimizer,
    PVLoader,
    PVAnalyzer,
    PVGeneration,
    GFILoader,
    GFISimulator,
    GFIAnalyzer,
    GFIPlotter,
    CombinedTDTools,
    DSSEAdapter,
    *_NETWORK_CLASSES,
)


@dataclass(frozen=True)
class ToolSpec:
    name: str
    callable: ToolCallable
    description: str = ""
    parameters: dict[str, Any] | None = None

    def call(self, arguments: dict[str, Any] | None = None) -> Any:
        return self.callable(**(arguments or {}))

    def as_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description or f"DistGrid-AgentBench tool: {self.name}",
                "parameters": self.parameters or generic_parameters_schema(),
            },
        }


class DistGridToolRegistry:
    def __init__(self, tools: Iterable[ToolSpec]):
        self._tools = {tool.name: tool for tool in tools}

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs(self) -> list[ToolSpec]:
        return [self._tools[name] for name in self.names()]

    def openai_tools(self) -> list[dict[str, Any]]:
        return [tool.as_openai_tool() for tool in self.specs()]

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        try:
            tool = self._tools[name]
        except KeyError as exc:
            known = ", ".join(self.names())
            raise KeyError(f"Unknown DistGrid-AgentBench tool '{name}'. Known tools: {known}") from exc
        return tool.call(arguments)


def load_tool_manifest(path: str | Path = "data/tool_manifest.json") -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generic_parameters_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {},
        "additionalProperties": True,
    }


def _json_schema_for_annotation(annotation: Any) -> dict[str, Any]:
    if annotation is inspect.Signature.empty or annotation is Any:
        return {}
    text = str(annotation).strip().strip("\"'")
    normalized = text.replace("typing.", "")
    lower = normalized.lower()
    if lower in {"str", "<class 'str'>"}:
        return {"type": "string"}
    if lower in {"int", "<class 'int'>"}:
        return {"type": "integer"}
    if lower in {"float", "<class 'float'>"}:
        return {"type": "number"}
    if lower in {"bool", "<class 'bool'>"}:
        return {"type": "boolean"}
    if lower.startswith("optional[") or lower.startswith("union["):
        inner = normalized[normalized.find("[") + 1 : -1].split(",", 1)[0]
        return _json_schema_for_annotation(inner)
    if lower.startswith(("list[", "tuple[", "set[")) or lower in {"list", "tuple", "set"}:
        return {"type": "array"}
    if lower.startswith("dict[") or lower in {"dict", "mapping"}:
        return {"type": "object"}
    if lower.startswith("literal["):
        quoted_values = re.findall(r"['\"]([^'\"]+)['\"]", normalized)
        if quoted_values:
            return {"type": "string", "enum": quoted_values}
    return {}


def _json_safe_default(value: Any) -> Any:
    try:
        json.dumps(value)
    except TypeError:
        return None
    return value


def parameters_schema_from_callable(func: ToolCallable) -> dict[str, Any]:
    signature = inspect.signature(func)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, parameter in signature.parameters.items():
        if name == "self" or parameter.kind in {
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        }:
            continue
        schema = _json_schema_for_annotation(parameter.annotation)
        if parameter.default is not inspect.Signature.empty:
            default = _json_safe_default(parameter.default)
            if default is not None:
                schema = {**schema, "default": default}
        else:
            required.append(name)
        properties[name] = schema
    output: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        output["required"] = required
    return output


def _manifest_by_name(manifest: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["name"]): dict(item) for item in manifest}


def _public_tool_specs(registry: SharedRegistry, manifest: list[dict[str, Any]]) -> list[ToolSpec]:
    manifest_by_name = _manifest_by_name(manifest)
    specs: list[ToolSpec] = []
    for cls in PUBLIC_TOOL_CLASSES:
        instance = cls(registry)
        for _, method in inspect.getmembers(instance, predicate=callable):
            if not getattr(method, "is_agent_tool", False):
                continue
            name = method.__name__
            metadata = manifest_by_name.get(name, {})
            specs.append(
                ToolSpec(
                    name=name,
                    callable=method,
                    description=str(metadata.get("description") or inspect.getdoc(method) or ""),
                    parameters=parameters_schema_from_callable(method),
                )
            )
    return specs


def build_tool_registry(
    *,
    manifest_path: str | Path = "data/tool_manifest.json",
) -> DistGridToolRegistry:
    manifest = load_tool_manifest(manifest_path)
    state = SharedRegistry()
    return DistGridToolRegistry(_public_tool_specs(state, manifest))

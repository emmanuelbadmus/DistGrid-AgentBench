#!/usr/bin/env python3
from __future__ import annotations
"""
DistGrid-AgentBench evaluator.

Scores an agent's results.jsonl against the canonical ground-truth workflows
and writes a per-task CSV.

Usage:
    python3 -m distgrid_bench.evaluate --results results.jsonl --gt_path benchmark
"""

import re
import json
import math
import argparse
import logging
import unicodedata
from pathlib import Path
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from distgrid_bench.tasks import load_benchmark_cases


logger = logging.getLogger("eval")

STATE_CHANGING_TOOLS = {
    "set_transformer_loading_limits",
    "set_cable_current_limits",
    "set_voltage_limits",
}


# =============================================================================
# Ground truth
# =============================================================================

def _benchmark_ground_truth_index(tasks_dir: Path) -> dict[int, dict]:
    cases = load_benchmark_cases(tasks_dir=tasks_dir)
    return {
        int(case.id): {
            "id": case.id,
            "task_family": case.task_family,
            "family_id": case.family_id,
            "query": case.query,
            "workflow": case.workflow,
        }
        for case in cases
    }


class GroundTruthResolver:
    def __init__(self, gt_path: Path):
        self._index: dict[int, dict] = self._load_index(gt_path)

    @staticmethod
    def _load_index(path: Path) -> dict[int, dict]:
        tasks_dir = path / "tasks" if (path / "tasks").is_dir() else path
        if (tasks_dir / "general" / "workflows.json").exists():
            return _benchmark_ground_truth_index(tasks_dir)
        flat = path / "evaluation_workflows.json"
        if flat.exists():
            items = json.loads(flat.read_text(encoding="utf-8"))
            return {int(item["id"]): item for item in items}
        return {}

    def resolve(self, query_id: int) -> Optional[dict]:
        return self._index.get(query_id)


# =============================================================================
# Workflow scoring
# =============================================================================

def normalize_query_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(text or ""))
    normalized = normalized.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", normalized).strip()


class WorkflowComparator:
    @staticmethod
    def _canonical_timestamp(value: Any) -> Optional[str]:
        from datetime import datetime
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        normalized = text.replace("T", " ")
        if normalized.endswith("Z"):
            normalized = normalized[:-1]
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d",
                    "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %I:%M:%S %p",
                    "%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M", "%m/%d/%Y"]:
            try:
                return datetime.strptime(normalized, fmt).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        return normalized.lower()

    @staticmethod
    def _is_numeric(value: Any) -> bool:
        if isinstance(value, bool):
            return False
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _numeric_match(av: Any, rv: Any, key: str) -> bool:
        strict_keys = {"tolerance", "noise_std_pu", "magnitude_pu",
                       "normalized_residual_threshold", "coverage",
                       "target_fraction", "max_iter", "top_k", "bins"}
        if key in strict_keys:
            return math.isclose(float(av), float(rv), rel_tol=1e-6, abs_tol=1e-9)
        return math.isclose(float(av), float(rv), rel_tol=1e-4, abs_tol=5e-5)

    @staticmethod
    def _normalize_arg(arg: Any) -> Any:
        if isinstance(arg, (list, tuple)):
            return [WorkflowComparator._normalize_arg(x) for x in arg]
        if isinstance(arg, dict):
            return {k: WorkflowComparator._normalize_arg(v) for k, v in arg.items()}
        if isinstance(arg, bool):
            return str(arg).lower()
        if WorkflowComparator._is_numeric(arg):
            return float(arg)
        return str(arg).lower()

    @staticmethod
    def _canonical_step(step: Dict[str, Any]) -> Tuple[str, str]:
        args = WorkflowComparator._normalize_arg(step.get("arguments", {}))
        return step.get("name", ""), json.dumps(args, sort_keys=True, default=str)

    @staticmethod
    def _collapse_idempotent_ref_steps(ref_wf: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        idempotent_tools = {
            "load_distribution_network", "load_load", "load_solar",
            "load_battery_specs", "load_pv_dataset", "load_transmission_network",
            "prepare_distribution_for_coupling", "load_dsse_case", "load_gfi_parameters",
        }
        seen: set = set()
        collapsed = []
        for step in ref_wf:
            key = WorkflowComparator._canonical_step(step)
            if step.get("name") in idempotent_tools and key in seen:
                continue
            seen.add(key)
            collapsed.append(step)
        return collapsed

    @staticmethod
    def _query_requests_arg(query_text: str, key: str, value: Any = None) -> bool:
        query = str(query_text or "").lower()
        if key == "solver":
            return "solver" in query or (value is not None and str(value).lower() in query)
        if key == "tolerance":
            return "tolerance" in query or re.search(r"\btol(?:erance)?\b", query) is not None
        if key == "max_iter":
            return "iteration" in query or ("max" in query and "iter" in query)
        if key == "strict":
            return "strict" in query
        return True

    @staticmethod
    def _query_requests_top_k(query_text: str, value: Any = None) -> bool:
        return "top" in str(query_text or "").lower()

    @staticmethod
    def _query_requests_sensitivity_variations(query_text: str) -> bool:
        query = str(query_text or "").lower()
        if "sensitivity" not in query:
            return False
        sensitivity_clause = query[query.find("sensitivity"):]
        signed_variations = re.findall(r"[-+]\s*\d+(?:\.\d+)?", sensitivity_clause)
        numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", sensitivity_clause)
        return "grid" in sensitivity_clause or len(signed_variations) >= 2 or len(numbers) >= 3

    @staticmethod
    def _query_allows_any_node_file_format(query_text: str) -> bool:
        query = str(query_text or "").lower()
        return ("machine-readable node list" in query
                and "json" not in query and "txt" not in query and "csv" not in query)

    @staticmethod
    def args_match(agent_args: Dict, ref_args: Dict, tool_name: str,
                   ref_feeder=None, query_text: str = "") -> Tuple[bool, str]:
        aa = agent_args.copy()
        ra = ref_args.copy()

        for k, v in ra.items():
            if k not in aa and v is None:
                aa[k] = None
        for k, v in list(aa.items()):
            if k not in ra and v is None:
                del aa[k]

        if tool_name == "load_solar":
            for k in ["feeder", "latitude", "longitude"]:
                aa.pop(k, None); ra.pop(k, None)

        if tool_name == "set_gfi_mode":
            gfi_defaults = {"K_droop_f": 20.0, "f_db": 0.0005, "K_droop_v": 20.0, "Vdb": 0.01}
            for key, default in gfi_defaults.items():
                if key in ra and (key not in aa or aa.get(key) is None):
                    if WorkflowComparator._is_numeric(ra[key]) and math.isclose(
                            float(ra[key]), default, rel_tol=1e-9, abs_tol=1e-12):
                        aa[key] = default

        if tool_name == "compare_strategies":
            for key in ("strategies",):
                if key in aa and key in ra:
                    aa[key] = ",".join(sorted(p.strip().lower() for p in str(aa.get(key, "")).split(",") if p.strip()))
                    ra[key] = ",".join(sorted(p.strip().lower() for p in str(ra.get(key, "")).split(",") if p.strip()))

        ignored_keys = {"backend", "capacity_override_kwh", "check_time",
                        "distribution_source_bus", "efficiency_override", "limit",
                        "path_glm", "path_raw", "power_override_kw", "save_path", "verbose"}

        if tool_name in {"solve", "run_combined_td_powerflow"}:
            for key in ("solver", "tolerance", "max_iter"):
                if key in ra and not WorkflowComparator._query_requests_arg(query_text, key, ra.get(key)):
                    ignored_keys.add(key)
        if tool_name == "audit_metadata_integrity":
            if "strict" in ra and not WorkflowComparator._query_requests_arg(query_text, "strict"):
                ignored_keys.add("strict")
        if tool_name == "summarize_ev_charger_placement":
            if "top_k" in ra and not WorkflowComparator._query_requests_top_k(query_text, ra.get("top_k")):
                ignored_keys.add("top_k")
        if tool_name == "export_data_to_file":
            export_type = str(ra.get("export_type") or aa.get("export_type") or "").lower()
            if export_type == "nodes" and WorkflowComparator._query_allows_any_node_file_format(query_text):
                ignored_keys.add("file_format")
        if tool_name == "run_sensitivity_analysis":
            if "variations_pct" in ra and not WorkflowComparator._query_requests_sensitivity_variations(query_text):
                ignored_keys.add("variations_pct")
        if tool_name == "load_load_profile":
            if ("hours_to_load" in ra
                    and WorkflowComparator._is_numeric(ra.get("hours_to_load"))
                    and math.isclose(float(ra.get("hours_to_load")), 24.0, rel_tol=1e-9, abs_tol=1e-12)
                    and aa.get("hours_to_load") is None):
                aa["hours_to_load"] = 24

        for k in ignored_keys:
            aa.pop(k, None); ra.pop(k, None)

        if "feeder" in aa and "feeder" in ra:
            af, rf = str(aa.get("feeder")), str(ra.get("feeder"))
            load_dist = tool_name == "prepare_distribution_for_coupling"
            if af != rf and not (load_dist and af == "active"):
                return False, "Feeder mismatch"

        for k in ra:
            if k not in aa:
                return False, f"Missing key {k}"

        csv_set_keys = {"chemistries", "strategies"}
        for k, rv in ra.items():
            av = aa.get(k)
            if k == "feeder" and tool_name == "prepare_distribution_for_coupling" and str(av) == "active":
                continue
            if k == "timestamp":
                if WorkflowComparator._canonical_timestamp(av) != WorkflowComparator._canonical_timestamp(rv):
                    return False, f"Mismatch {k}: {av} != {rv}"
                continue
            if k in csv_set_keys:
                av_set = {p.strip().lower() for p in str(av or "").split(",") if p.strip()}
                rv_set = {p.strip().lower() for p in str(rv or "").split(",") if p.strip()}
                if av_set != rv_set:
                    return False, f"Mismatch {k}: {av} != {rv}"
                continue
            if WorkflowComparator._is_numeric(av) and WorkflowComparator._is_numeric(rv):
                if not WorkflowComparator._numeric_match(av, rv, k):
                    return False, f"Mismatch {k}: {av} != {rv}"
                continue
            if WorkflowComparator._normalize_arg(av) != WorkflowComparator._normalize_arg(rv):
                return False, f"Mismatch {k}: {av} != {rv}"
        return True, ""

    @staticmethod
    def _network_loaded_implicitly(agent_wf: List[Dict], ref_step: Dict) -> bool:
        if ref_step.get("name") != "load_distribution_network":
            return False
        ref_feeder = str((ref_step.get("arguments", {}) or {}).get("feeder", "")).lower()
        if not ref_feeder:
            return False
        network_dependent_tools = {
            "calculate_total_power", "check_voltage_violations",
            "export_nodes_by_voltage_condition", "get_bus_voltages", "plot_network_data",
        }
        feeder_seen = any(
            str((step.get("arguments", {}) or {}).get("feeder", "")).lower() == ref_feeder
            for step in agent_wf if step.get("name") in {"load_load", "load_solar"}
        )
        dependent_success = any(
            step.get("name") in network_dependent_tools and step.get("success") is not False
            for step in agent_wf
        )
        return feeder_seen and dependent_success

    @staticmethod
    def analyze(agent_wf: List[Dict], ref_wf: List[Dict], query_text: str = "") -> Tuple[bool, str, float]:
        """
        Returns (success, reason, precision).
        success (P@1): True if all ground-truth tools are present and matched.
        precision: 1.0 only if the agent made no extra tool calls beyond the GT.
        """
        ref_wf = WorkflowComparator._collapse_idempotent_ref_steps(ref_wf)
        agent_wf = WorkflowComparator._collapse_idempotent_ref_steps(agent_wf)

        dedup = []
        last_idxs = {s["name"]: i for i, s in enumerate(agent_wf) if s["name"] in STATE_CHANGING_TOOLS}
        for i, s in enumerate(agent_wf):
            if s["name"] not in STATE_CHANGING_TOOLS or last_idxs[s["name"]] == i:
                dedup.append(s)
        agent_wf = dedup

        if not ref_wf:
            return True, "", 0.0 if agent_wf else 1.0

        ref_feeder = next(
            (s["arguments"].get("feeder") for s in ref_wf if s["name"] == "load_distribution_network"), None
        )

        agent_matched: set[int] = set()
        failure_reasons: list[str] = []

        for ref_step in ref_wf:
            ref_name = ref_step["name"]
            found = False
            mismatch_reasons: list[str] = []
            for idx, agent_step in enumerate(agent_wf):
                if idx in agent_matched:
                    continue
                if agent_step["name"] == ref_name:
                    valid, msg = WorkflowComparator.args_match(
                        agent_step.get("arguments", {}),
                        ref_step.get("arguments", {}),
                        ref_name, ref_feeder, query_text,
                    )
                    if valid:
                        if agent_step.get("success") is False:
                            continue
                        agent_matched.add(idx)
                        found = True
                        break
                    if msg and msg not in mismatch_reasons:
                        mismatch_reasons.append(msg)

            if not found and WorkflowComparator._network_loaded_implicitly(agent_wf, ref_step):
                found = True
            if not found and ref_step.get("name") == "set_gfi_mode":
                ref_args = ref_step.get("arguments", {}) or {}
                mode = str(ref_args.get("mode", "")).lower()
                if mode in {"pq", "base_pq"} and all(v in (None, "") for v in
                                                       [v for k, v in ref_args.items() if k != "mode"]):
                    found = True
            if not found:
                reason = (f"Missing/mismatched tool {ref_name}: {'; '.join(mismatch_reasons)}"
                          if mismatch_reasons else f"Missing tool {ref_name}")
                failure_reasons.append(reason)

        if failure_reasons:
            return False, " | ".join(failure_reasons), 0.0

        has_extras = any(idx not in agent_matched for idx in range(len(agent_wf)))
        precision = 0.0 if has_extras else 1.0
        return True, "", precision


# =============================================================================
# Evaluator
# =============================================================================

def _workflow_from_tool_traces(tool_traces: list[dict]) -> list[dict]:
    return [
        {"name": t.get("name"), "arguments": t.get("args", {}), "success": bool(t.get("success", True))}
        for t in tool_traces
        if not t.get("blocked")
    ]


class Evaluator:
    def __init__(self, results_path: Path, gt_path: Path, allow_query_text_mismatch: bool = False):
        self.results_path = results_path
        self.gt = GroundTruthResolver(gt_path)
        self.allow_query_text_mismatch = allow_query_text_mismatch

    def evaluate(self) -> pd.DataFrame:
        rows = []
        for line in self.results_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed line: {e}")
                continue

            query_id = int(data["query_id"])
            ref = self.gt.resolve(query_id)
            if ref is None:
                logger.warning(f"No ground truth for query_id={query_id}")
                continue

            agent_wf = _workflow_from_tool_traces(data.get("tool_traces", []))
            gt_wf = ref.get("workflow", [])
            ref_query = normalize_query_text(str(ref.get("query", "")))
            run_query = normalize_query_text(str(data.get("query", "")))

            if (not self.allow_query_text_mismatch and ref_query and run_query
                    and ref_query != run_query):
                success, reason, precision = False, "Query text mismatch with ground truth", 0.0
            elif data.get("error") or not data.get("success", True):
                success, reason, precision = False, str(data.get("error") or "Run failed"), 0.0
            else:
                success, reason, precision = WorkflowComparator.analyze(agent_wf, gt_wf, ref_query)

            agent_tools = [s.get("name") for s in agent_wf]
            gt_tools = [s.get("name") for s in gt_wf]
            agent_counts = Counter(agent_tools)
            gt_counts = Counter(gt_tools)

            rows.append({
                "query_id": f"{query_id:03d}",
                "task_family": ref.get("task_family", ""),
                "query": ref_query,
                "success": 1 if success else 0,
                "precision": precision,
                "failure_reason": reason,
                "tool_calls": len(agent_wf),
                "missing_tools": json.dumps(sorted(t for t, c in gt_counts.items() if agent_counts[t] < c)),
                "extra_tools": json.dumps(sorted(t for t, c in agent_counts.items() if gt_counts[t] < c)),
                "final_answer": str(data.get("final_answer") or ""),
                "model": str(data.get("model") or ""),
            })

        return pd.DataFrame(rows)


# =============================================================================
# CLI
# =============================================================================

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate agent results against DistGrid-AgentBench ground truth.")
    parser.add_argument("--results", default="results.jsonl", help="Path to agent results.jsonl")
    parser.add_argument("--gt_path", default="benchmark", help="Path to benchmark root (contains tasks/)")
    parser.add_argument("--output", default="evaluation", help="Output directory for results CSV")
    parser.add_argument("--allow-query-text-mismatch", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()] if args.verbose else [logging.NullHandler()],
    )

    results_path = Path(args.results)
    if not results_path.exists():
        print(f"Error: results file not found: {results_path}")
        return 1

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    evaluator = Evaluator(results_path, Path(args.gt_path), args.allow_query_text_mismatch)
    df = evaluator.evaluate()

    if df.empty:
        print("No results found.")
        return 1

    df["success"] = pd.to_numeric(df["success"], errors="coerce").fillna(0)
    df["precision"] = pd.to_numeric(df["precision"], errors="coerce").fillna(0)

    csv_path = out_dir / "per_task_results.csv"
    df.to_csv(csv_path, index=False)

    # Summary
    n = len(df)
    p_at_1 = df["success"].mean() * 100
    precision = df["precision"].mean() * 100
    print(f"\nResults: {n} tasks | P@1={p_at_1:.1f}% | Precision={precision:.1f}%")

    if "task_family" in df.columns:
        print("\nBy family:")
        for family, group in df.groupby("task_family"):
            print(f"  {family:<15} P@1={group['success'].mean()*100:.1f}%  ({int(group['success'].sum())}/{len(group)})")

    failed = df[df["success"] == 0]
    if not failed.empty:
        print(f"\nFailed ({len(failed)}):")
        for _, row in failed.sort_values("query_id").iterrows():
            print(f"  {row['query_id']}: {row['failure_reason']}")

    print(f"\nDetailed results saved to {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

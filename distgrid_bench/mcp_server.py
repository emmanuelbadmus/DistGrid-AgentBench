#!/usr/bin/env python3
"""MCP server exposing all DistGrid-AgentBench tools over stdio."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool

from distgrid_bench.tools.registry import build_tool_registry

_registry = build_tool_registry()
server = Server("distgrid-agentbench")


@server.list_tools()
async def list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name=spec.name,
                description=spec.description,
                inputSchema=spec.parameters or {"type": "object", "properties": {}},
            )
            for spec in _registry.specs()
        ]
    )


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> CallToolResult:
    try:
        result = _registry.call(name, arguments)
        text = result if isinstance(result, str) else json.dumps(result, default=str)
    except Exception as exc:
        text = f"Error: {exc}"
    return CallToolResult(content=[TextContent(type="text", text=text)])


async def _serve() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    asyncio.run(_serve())


if __name__ == "__main__":
    main()

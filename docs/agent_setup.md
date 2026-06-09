# Connecting Your Agent to DistGrid-AgentBench

DistGrid-AgentBench exposes all 108 tools as an MCP server. Any MCP-compatible
agent can connect to it directly — no custom integration code required.

## Prerequisites

Clone the repo, then install:

```bash
git clone https://github.com/emmanuelbadmus/DistGrid-AgentBench
cd DistGrid-AgentBench
pip install -r requirements.txt
pip install -e ".[mcp,optimization]"
```

> **Windows:** use `python` instead of `python3` throughout this guide.
> **Linux/macOS:** use `python3`.

Confirm it works:

```bash
python3 -m distgrid_bench.mcp_server
# Should start silently (waiting for MCP input over stdio)
```

### What the extras include

| Extra | What it enables |
|---|---|
| `mcp` | MCP server (`distgrid_bench.mcp_server`) |
| `optimization` | GFI simulation tools (requires pyomo) |
| `geospatial` | PV utility territory tools (requires geopandas) |

**Minimum install** — `pip install -e ".[mcp]"` is enough to start the MCP server and run BESS, PV (basic), and network analysis tools (if network package is available).

**Full public install** — `pip install -e ".[mcp,optimization]"` covers all publicly available tool families.

---

## Benchmark family availability

| Family | Runnable without proprietary data? | Requires |
|---|---|---|
| BESS | Yes | base install |
| PV | Yes | base install |
| GFI | Yes | `optimization` extra |
| General | Partial (network queries blocked) | network package |
| Powerflow | Partial | network package |
| Combined T&D | No | network package + feeder data |
| DHC | No | network package + feeder data |
| DSSE | No | network package + feeder data |
| EV | No | network package + feeder data |
| Infeasibility | No | network package + feeder data |

The network package and feeder data are proprietary — contact the authors for access.

---

## Claude Desktop

Add the server to your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "distgrid-agentbench": {
      "command": "python3",
      "args": ["-m", "distgrid_bench.mcp_server"]
    }
  }
}
```

Restart Claude Desktop. All available tools will appear automatically.

---

## Claude Code

Run once inside the repo:

```bash
claude mcp add distgrid-agentbench -- python3 -m distgrid_bench.mcp_server
```

Or add to your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "distgrid-agentbench": {
      "command": "python3",
      "args": ["-m", "distgrid_bench.mcp_server"]
    }
  }
}
```

---

## Codex CLI

In your `codex.config.json`:

```json
{
  "mcpServers": {
    "distgrid-agentbench": {
      "command": "python3",
      "args": ["-m", "distgrid_bench.mcp_server"]
    }
  }
}
```

---

## LangChain

Install the MCP adapter:

```bash
pip install langchain-mcp-adapters
```

```python
from mcp import StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

server_params = StdioServerParameters(
    command="python3",
    args=["-m", "distgrid_bench.mcp_server"],
)

async def run():
    async with load_mcp_tools(server_params) as tools:
        model = ChatOpenAI(model="gpt-4o")
        agent = create_react_agent(model, tools)
        result = await agent.ainvoke({
            "messages": "How many capacitors are in the Rochester feeder?"
        })
        print(result["messages"][-1].content)
```

---

## Custom Python Agent

For programmatic or eval harness use, skip MCP and use the registry directly:

```python
import json
from distgrid_bench.tools.registry import build_tool_registry

registry = build_tool_registry()
tools_for_model = registry.openai_tools()  # OpenAI / Anthropic format

tasks = [json.loads(line) for line in open("benchmark/tasks.jsonl")]

for task in tasks:
    query = task["query"]
    # send query + tools_for_model to your model
    # when the model requests a tool call:
    result = registry.call("analyze_bess_performance", {})
```

---

## Data directory

By default, tools look for input data under `data/` relative to the working
directory. Override this if your data lives elsewhere:

```bash
# Linux / macOS
export DISTGRID_BENCH_DATA_DIR=/path/to/your/data

# Windows
set DISTGRID_BENCH_DATA_DIR=C:\path\to\your\data
```

---

## Evaluating a Run

After your agent produces results, write one JSON object per line to `results.jsonl`:

```json
{
  "query_id": 1,
  "query": "How many capacitors are in the Rochester feeder?",
  "model": "openai:gpt-4o",
  "mode": "react",
  "success": true,
  "tool_traces": [
    {"name": "load_distribution_network", "args": {"feeder": "rochester"}, "success": true, "elapsed_s": 0.14}
  ],
  "final_answer": "There are 3 capacitors."
}
```

Then evaluate:

```bash
python3 -m distgrid_bench.evaluate --results results.jsonl --gt_path benchmark
```

Results are written to `evaluation/per_task_results.csv`. A summary with P@1 and precision per task family is also printed to the terminal.

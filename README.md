# DistGrid-AgentBench: A Distribution Grid Benchmark for Agentic AI

DistGrid-AgentBench is a benchmark and evaluation harness for agentic distribution-grid
workflows. It follows the Tau-Bench style separation between agents and the
environment: agents interact with a documented tool API, while the benchmark owns
tasks, traces, result formats, and scoring.

This repository contains:

- 200 benchmark tasks across ten task families, each with the query and canonical
  ground-truth workflow co-located as `benchmark/tasks/{family}/workflows.json`;
- a runner-agnostic tool registry and an evaluator that scores any agent's run.

> **Note:** The feeder network data (`data/inputs/feeders/`), utility GIS data
> (`data/inputs/geopackage/`), and the network tool implementations
> (`distgrid_bench/tools/network/`) are proprietary and not included in this
> repository.

## Quickstart

```bash
git clone https://github.com/emmanuelbadmus/DistGrid-AgentBench
cd DistGrid-AgentBench
pip install -r requirements.txt
pip install -e ".[mcp,optimization]"
```

See [docs/agent_setup.md](docs/agent_setup.md) for connecting to your agent.

## Repository Layout

```text
distgrid_bench/
  tasks.py              # task loading helpers
  evaluate.py           # scoring and result summarization
  tools/
    registry.py         # DistGridToolRegistry + build_tool_registry()
    shared_registry.py  # SharedRegistry (tool state)
    tool_config.py      # paths and config maps
    decorators.py       # @agent_tool decorator
    bess_analysis.py    # BESS tools
    pv_analysis.py      # PV tools
    gfi_analysis.py     # GFI tools
    dsse_adapter.py     # DSSE tools
    combined_td.py      # combined T&D tools
    network/            # network tools — proprietary, not included
benchmark/
  tasks.jsonl           # 200 tasks: {id, family, query} — the agent interface
  tasks/                # ground truth + reference solutions (used by the evaluator)
    bess/
      workflows.json    # canonical workflows for scoring
      1.py … 20.py      # reference solution scripts
    general/  ev/  pv/  gfi/  dsse/  dhc/  powerflow/  infeasibility/  combined_td/
data/
  tool_manifest.json    # tool catalog (name + description for all 108 tools)
  inputs/
    bess/               # BESS battery specs, load profiles, tariffs
    gfi/                # GFI parameters
    feeders/            # feeder network data — proprietary, not included
    geopackage/         # utility GIS data — proprietary, not included
```

## Benchmark Set

Ten task families, 20 cases each, 200 total:

- general, powerflow, infeasibility, DHC, EV, BESS, PV, GFI, combined T&D, DSSE

`benchmark/tasks.jsonl` is the agent-facing task file — one JSON object per line:

```json
{"id": "001", "family": "general", "query": "How many capacitors are in the Rochester feeder?"}
```

The corresponding ground-truth workflow and reference solution script live in
`benchmark/tasks/{family}/` alongside each other.

Each family contains 20 numbered Python scripts (`1.py` through `20.py`) that are the
human-expert reference solutions — they show exactly how a domain expert would solve
each task using the tool API. You can run any of them directly to see the expected
tool sequence and output:

```bash
python3 benchmark/tasks/bess/1.py
python3 benchmark/tasks/gfi/5.py
python3 benchmark/tasks/pv/12.py
```

These scripts serve two purposes: they are the executable ground truth that a perfect
agent should replicate, and they are a learning resource showing correct tool usage
for each task family. Note that scripts in network-dependent families (general,
powerflow, infeasibility, dhc, ev, combined_td, dsse) require the proprietary
network package and feeder data to run — see [Known Limitations](#known-limitations).

## Tool API

108 benchmark tools are listed in `data/tool_manifest.json`. Every tool runs
locally — `build_tool_registry()` instantiates them all in-process:

```python
from distgrid_bench.tools.registry import build_tool_registry

registry = build_tool_registry()
tools_for_model = registry.openai_tools()
result = registry.call("load_distribution_network", {"feeder": "rochester"})
```

## Agent Integration

All 108 tools are exposed as an MCP server — point any MCP-compatible agent at it
with no custom integration code:

```bash
pip install -e ".[mcp,optimization]"
python3 -m distgrid_bench.mcp_server
```

See [docs/agent_setup.md](docs/agent_setup.md) for setup instructions for Claude Desktop,
Claude Code, Codex, LangChain, and custom agents.

## Evaluating a Run

Write one JSON object per line to `results.jsonl`:

```json
{
  "query_id": 1,
  "query": "user task text",
  "model": "provider:model",
  "mode": "your_agent_name",
  "success": true,
  "tool_traces": [{"name": "load_distribution_network", "args": {"feeder": "rochester"}, "success": true, "elapsed_s": 0.14}],
  "final_answer": "..."
}
```

Then run:

```bash
python3 -m distgrid_bench.evaluate --results results.jsonl --gt_path benchmark
```

The evaluator scores each run against the canonical ground-truth workflows,
prints P@1 and precision per task family, and writes `evaluation/per_task_results.csv`.

## Known Limitations

**Partial benchmark coverage without proprietary data.**
Only 3 of 10 task families are fully runnable from a public install: BESS, PV (basic), and GFI. The remaining 7 families (General, Powerflow, Infeasibility, DHC, EV, Combined T&D, DSSE) depend on the proprietary feeder network data (`data/inputs/feeders/`) and network tool package (`distgrid_bench/tools/network/`). Tasks in those families can still be sent to an agent; the tools will return an error explaining what is missing rather than silently failing.

**Reference scripts for network-dependent families require the proprietary package.**
`1.py`–`20.py` scripts in BESS, PV, and GFI families run on a public install. Scripts
in the remaining 7 families (General, Powerflow, Infeasibility, DHC, EV, Combined T&D,
DSSE) import from `distgrid_bench.tools.network` and require the proprietary network
package and feeder data. The ground-truth workflow JSON (`workflows.json`) is available
for all families regardless — the evaluator uses that, not the scripts.

**GFI simulation requires an optional install.**
The `run_gfi_simulation` tool requires pyomo. Install with `pip install -e ".[optimization]"` or `pip install pyomo`. Without it, the tool returns a descriptive error string rather than crashing.

**Feeder names are specific to the included dataset.**
The four feeders in the benchmark tasks (rochester, stowe, south_hero, glover) are real Vermont distribution feeders. Users with access to the proprietary data must place files at the expected paths under `data/inputs/feeders/`, or override the root with `DISTGRID_BENCH_DATA_DIR`. The tool registry itself is not tied to these feeders — the scoring logic accepts any tool calls with matching arguments.

**Fixed task count.**
`tasks.py` enforces exactly 20 tasks per family and 200 total. If you fork the benchmark and add or remove tasks, update the assertions in `load_benchmark_cases()` accordingly.

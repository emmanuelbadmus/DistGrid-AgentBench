from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

TASK_FAMILIES: tuple[str, ...] = (
    "general",
    "powerflow",
    "infeasibility",
    "dhc",
    "ev",
    "bess",
    "pv",
    "gfi",
    "combined_td",
    "dsse",
)

TASK_FAMILY_LABELS: dict[str, str] = {
    "general": "General",
    "powerflow": "Powerflow",
    "infeasibility": "Infeasibility",
    "dhc": "DHC",
    "ev": "EV",
    "bess": "BESS",
    "pv": "PV",
    "gfi": "GFI",
    "combined_td": "Combined T&D",
    "dsse": "DSSE",
}


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    task_family: str
    family_id: str
    query: str
    workflow: list[dict]


def load_benchmark_cases(
    *,
    tasks_dir: str | Path = "benchmark/tasks",
    families: tuple[str, ...] = TASK_FAMILIES,
) -> list[BenchmarkCase]:
    root = Path(tasks_dir)
    cases: list[BenchmarkCase] = []
    global_id = 1
    for family in families:
        workflow_path = root / family / "workflows.json"
        workflows = json.loads(workflow_path.read_text(encoding="utf-8"))
        if len(workflows) != 20:
            raise ValueError(f"{workflow_path} must contain exactly 20 entries, found {len(workflows)}")
        for entry in workflows:
            family_id = str(entry["id"]).zfill(3)
            query = str(entry.get("query") or "").strip()
            if not query:
                raise ValueError(f"{workflow_path} entry {family_id} has no query text")
            cases.append(
                BenchmarkCase(
                    id=f"{global_id:03d}",
                    task_family=family,
                    family_id=family_id,
                    query=query,
                    workflow=list(entry.get("workflow") or []),
                )
            )
            global_id += 1
    if len(cases) != 200:
        raise ValueError(f"Expected 200 benchmark cases, found {len(cases)}")
    return cases


def benchmark_cases_to_records(cases: list[BenchmarkCase]) -> list[dict]:
    return [
        {
            "id": case.id,
            "task_family": case.task_family,
            "family_id": case.family_id,
            "query": case.query,
            "workflow": case.workflow,
        }
        for case in cases
    ]

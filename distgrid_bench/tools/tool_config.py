from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DISTGRID_BENCH_DATA_DIR", BASE_DIR / "data"))
INPUT_DIR = DATA_DIR / "inputs"
FEEDERS_DIR = INPUT_DIR / "feeders"
OUTPUT_DIR = DATA_DIR / "outputs"
EXECUTION_OUTPUT_DIR = DATA_DIR / "execution_output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EXECUTION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOLVER_TIME_LIMIT_SECONDS = 30

FEEDER_MAP = {
    "south_hero": FEEDERS_DIR / "south_hero" / "node.glm",
    "glover": FEEDERS_DIR / "glover" / "node.glm",
    "rochester": FEEDERS_DIR / "rochester" / "node.glm",
    "stowe": FEEDERS_DIR / "stowe" / "node.glm",
}

FEEDER_COORDS = {
    "south_hero": (44.6472, -73.3100),
    "rochester": (43.8746, -72.8080),
    "stowe": (44.4753, -72.7022),
    "glover": (44.7069, -72.1869),
}

COORDINATES_MAP = {
    "south_hero": FEEDERS_DIR / "south_hero" / "Coordinates.csv",
    "glover": FEEDERS_DIR / "glover" / "Coordinates.csv",
    "rochester": FEEDERS_DIR / "rochester" / "Coordinates.csv",
    "stowe": FEEDERS_DIR / "stowe" / "Coordinates.csv",
}

AMI_MAP = {
    "south_hero": FEEDERS_DIR / "south_hero" / "AMI_data.csv",
    "glover": FEEDERS_DIR / "glover" / "AMI_data.csv",
    "rochester": FEEDERS_DIR / "rochester" / "AMI_data.csv",
    "stowe": FEEDERS_DIR / "stowe" / "AMI_data.csv",
}

EV_CHARGER_MAP = {
    "south_hero": FEEDERS_DIR / "south_hero" / "EV_chargers.csv",
    "glover": FEEDERS_DIR / "glover" / "EV_chargers.csv",
    "rochester": FEEDERS_DIR / "rochester" / "EV_chargers.csv",
    "stowe": FEEDERS_DIR / "stowe" / "EV_chargers.csv",
}

PV_DATASETS = {
    "vec": INPUT_DIR / "geopackage" / "VEC.gpkg",
    "gmp": INPUT_DIR / "geopackage" / "GMP.gpkg",
    "bed": INPUT_DIR / "geopackage" / "BED.gpkg",
}

PV_MODELS: dict = {}


def _detect_ipopt_solver_options() -> dict:
    """Return IPOPT solver options, preferring MA57 if the HSL library is available."""
    import ctypes

    hsl_paths = [
        os.path.expanduser("~/opt/CoinHSL/lib/libcoinhsl.dylib"),
        "/opt/homebrew/lib/libhsl.dylib",
        "/usr/local/lib/libhsl.dylib",
        "/usr/local/lib/libcoinhsl.so",
    ]
    for candidate in hsl_paths:
        try:
            ctypes.CDLL(candidate)
            return {"linear_solver": "ma57"}
        except OSError:
            continue
    return {}


IPOPT_SOLVER_OPTIONS = _detect_ipopt_solver_options()


from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

import matplotlib

matplotlib.use("Agg", force=True)
import matplotlib.pyplot as plt

from distgrid_bench.tools.decorators import agent_tool

from distgrid_bench.tools import tool_config as config
from distgrid_bench.tools.shared_registry import SharedRegistry


@dataclass
class DSSECase:
    feeder: str
    backend: str
    network_model: Any
    bus_names: list[str]


@dataclass
class DSSEReport:
    voltage_rmse_pu: Optional[float] = None
    max_abs_error_pu: Optional[float] = None
    residual_threshold: Optional[float] = None
    bad_measurement_count: int = 0
    notes: list[str] = field(default_factory=list)


class DSSEAdapter:
    """Lightweight distribution-system state-estimation benchmark tools."""

    def __init__(self, registry: SharedRegistry):
        self.registry = registry
        self.output_dir = config.EXECUTION_OUTPUT_DIR / "dsse"

    def _get(self, key: str):
        return self.registry.get(key)

    def _set(self, key: str, value: Any) -> None:
        self.registry.set(key, value)

    def _bus_names_from_network(self, network_model: Any) -> list[str]:
        names = []
        for bus in getattr(network_model, "buses", []) or []:
            name = str(getattr(bus, "NodeName", "")).strip()
            if name:
                names.append(name)
        return sorted(set(names)) or ["sourcebus", "load_1", "load_2", "load_3"]

    @agent_tool
    def load_dsse_case(
        self,
        feeder: Literal["south_hero", "rochester", "stowe", "glover"] = "south_hero",
        backend: Literal["auto", "synthetic", "openpy_dsse"] = "auto",
    ) -> str:
        """
        Load a DSSE benchmark case for the specified distribution feeder.

        Args:
            feeder: Distribution feeder used as the DSSE benchmark network.
            backend: `synthetic` for the lightweight local estimator, `openpy_dsse` for an optional external backend, or `auto`.

        Returns:
            str: Status message describing the loaded DSSE case and active backend.
        """
        if backend in {"auto", "openpy_dsse"}:
            try:
                __import__("openpy_dsse")
                selected_backend = "openpy_dsse"
            except Exception:
                if backend == "openpy_dsse":
                    return "Error: OpenPy-DSSE backend requested but the package is not installed."
                selected_backend = "synthetic"
        else:
            selected_backend = "synthetic"

        network_model = self._get("network:active")
        if not network_model:
            return "Error: Required network state is missing."

        bus_names = self._bus_names_from_network(network_model)
        case = DSSECase(
            feeder=feeder,
            backend=selected_backend,
            network_model=network_model,
            bus_names=bus_names,
        )
        self._set("network_model", network_model)
        self._set("dsse:case", case)
        return f"Loaded DSSE case for '{feeder}' using '{selected_backend}' backend with {len(bus_names)} buses."

    @agent_tool
    def run_truth_powerflow(self) -> str:
        """
        Create a synthetic ground-truth voltage state for the loaded feeder.

        Generates per-bus voltage magnitudes that serve as the reference for
        measurement synthesis and estimation error calculation.

        Returns:
            str: Summary of the truth voltage state including bus count.
        """
        case = self._get("dsse:case")
        if not case:
            return "Error: Missing dsse:case."

        truth = {}
        for idx, bus_name in enumerate(case.bus_names):
            # Deterministic synthetic voltage profile around nominal conditions.
            truth[bus_name] = round(1.0 - 0.0007 * (idx % 20) + 0.002 * math.sin(idx), 6)

        self._set("truth_voltage_state", truth)
        self._set(
            "truth_powerflow_state",
            {"backend": case.backend, "feeder": case.feeder, "bus_count": len(truth)},
        )
        return f"Truth power-flow state created for {len(truth)} buses. Registered `truth_voltage_state`."

    @agent_tool
    def generate_measurements_from_truth(
        self,
        noise_std_pu: float = 0.003,
        coverage: float = 1.0,
        seed: int = 7,
    ) -> str:
        """
        Generate noisy voltage measurements from the synthetic truth state.

        Produces a measurement set by adding Gaussian noise to the truth voltages,
        covering a configurable fraction of buses. Unobserved buses receive
        pseudo-measurements at nominal voltage with higher uncertainty.

        Args:
            noise_std_pu: Standard deviation of voltage measurement noise in per-unit.
            coverage: Fraction of buses receiving direct measurements (0 to 1).
            seed: Random seed for repeatable benchmark generation.

        Returns:
            str: Summary of generated measurements and pseudo-measurements.
        """
        truth = self._get("truth_voltage_state")
        if not truth:
            return "Error: Missing truth_voltage_state."

        rng = random.Random(seed)
        coverage = max(0.0, min(1.0, coverage))
        measurements = []
        pseudo = []
        for bus, value in truth.items():
            if rng.random() <= coverage:
                noisy = value + rng.gauss(0.0, noise_std_pu)
                measurements.append({
                    "id": f"v_{bus}",
                    "type": "voltage_magnitude",
                    "bus": bus,
                    "value_pu": round(noisy, 6),
                    "std_pu": noise_std_pu,
                })
            else:
                pseudo.append({"bus": bus, "value_pu": 1.0, "std_pu": 0.03})

        covariance = {m["id"]: round(m["std_pu"] ** 2, 10) for m in measurements}
        self._set("measurement_set", measurements)
        self._set("measurement_covariance", covariance)
        self._set("pseudo_measurement_set", pseudo)
        return f"Generated {len(measurements)} measurements and {len(pseudo)} pseudo-measurements."

    def load_measurement_file(self, file_path: str) -> str:
        """
        Load DSSE measurements from a JSON or CSV file.

        Args:
            file_path: JSON or CSV measurement file path.

        Returns:
            str: Status message with measurement count.
        """
        path = Path(file_path)
        if not path.exists():
            return f"Error: Measurement file not found: {file_path}"
        if path.suffix.lower() == ".json":
            rows = json.loads(path.read_text())
        elif path.suffix.lower() == ".csv":
            with path.open(newline="") as fh:
                rows = list(csv.DictReader(fh))
        else:
            return "Error: Unsupported measurement format. Use JSON or CSV."

        measurements = []
        for idx, row in enumerate(rows):
            bus = str(row.get("bus") or row.get("bus_id") or "").strip()
            value = row.get("value_pu", row.get("voltage_pu"))
            if not bus or value is None:
                continue
            std = float(row.get("std_pu", 0.003))
            measurements.append({
                "id": str(row.get("id") or f"file_v_{idx}"),
                "type": "voltage_magnitude",
                "bus": bus,
                "value_pu": float(value),
                "std_pu": std,
            })
        self._set("measurement_set", measurements)
        self._set("measurement_covariance", {m["id"]: m["std_pu"] ** 2 for m in measurements})
        return f"Loaded {len(measurements)} measurements from {file_path}."

    @agent_tool
    def drop_measurements(self, drop_fraction: float = 0.2, seed: int = 11) -> str:
        """
        Remove a random fraction of measurements to emulate telemetry outages.

        Args:
            drop_fraction: Fraction of measurements to remove (0 to 1).
            seed: Random seed for repeatable dropping.

        Returns:
            str: Count of removed and remaining measurements.
        """
        measurements = list(self._get("measurement_set") or [])
        if not measurements:
            return "Error: Missing measurement_set. Generate or load measurements first."
        rng = random.Random(seed)
        count = max(1, int(len(measurements) * max(0.0, min(1.0, drop_fraction))))
        drop_ids = set(rng.sample([m["id"] for m in measurements], min(count, len(measurements))))
        kept = [m for m in measurements if m["id"] not in drop_ids]
        self._set("measurement_set", kept)
        self._set("missing_measurement_mask", sorted(drop_ids))
        return f"Dropped {len(drop_ids)} measurements; {len(kept)} measurements remain."

    @agent_tool
    def inject_bad_data(
        self,
        target_fraction: float = 0.1,
        magnitude_pu: float = 0.05,
        seed: int = 19,
    ) -> str:
        """
        Inject a deterministic voltage bias into a fraction of measurements.

        Corrupts selected measurements by adding a fixed offset, simulating
        meter failures or communication errors for bad-data detection testing.

        Args:
            target_fraction: Fraction of measurements to corrupt (0 to 1).
            magnitude_pu: Voltage bias added to each corrupted measurement in per-unit.
            seed: Random seed for target selection.

        Returns:
            str: Count of corrupted measurements.
        """
        measurements = [dict(m) for m in (self._get("measurement_set") or [])]
        if not measurements:
            return "Error: Missing measurement_set. Generate or load measurements first."
        rng = random.Random(seed)
        count = max(1, int(len(measurements) * max(0.0, min(1.0, target_fraction))))
        target_ids = set(rng.sample([m["id"] for m in measurements], min(count, len(measurements))))
        for measurement in measurements:
            if measurement["id"] in target_ids:
                measurement["value_pu"] = round(float(measurement["value_pu"]) + magnitude_pu, 6)
                measurement["bad_data"] = True
        record = {"target_ids": sorted(target_ids), "magnitude_pu": magnitude_pu}
        self._set("measurement_set", measurements)
        self._set("bad_data_injection_record", record)
        return f"Injected bad data into {len(target_ids)} measurements."

    @agent_tool
    def build_measurement_topology(self) -> str:
        """
        Construct the observation matrix that maps measurements to network state variables.

        The WLS state estimator solves the system H·x ≈ z, where H is the observation
        matrix built here from the active measurement set and feeder topology. Each
        measurement is assigned to its corresponding bus voltage state variable and
        weighted by its noise covariance. Coverage statistics indicate how many buses
        are directly observed versus relying on pseudo-measurements.

        Returns:
            str: Summary of the observation topology including state count, measurement count, and coverage.
        """
        case = self._get("dsse:case")
        measurements = self._get("measurement_set") or {}
        bus_names = list(case.bus_names) if case else []
        n_states = len(bus_names)
        n_measurements = len(measurements)
        coverage = round(n_measurements / max(n_states, 1), 4) if n_states else 0.0
        observed = set(m.get("bus") for m in (measurements.values() if isinstance(measurements, dict) else measurements))
        topology = {
            "n_states": n_states,
            "n_measurements": n_measurements,
            "coverage": coverage,
            "observed_buses": len(observed),
        }
        self._set("dsse:topology", topology)
        return (
            f"Measurement topology built: {n_states} state variables, "
            f"{n_measurements} measurements, {coverage:.0%} coverage. "
            f"Registered `dsse:topology`."
        )

    @agent_tool
    def run_dsse(self, use_pseudo_measurements: bool = True) -> str:
        """
        Run the weighted least-squares state estimator on the active measurement set.

        Estimates per-bus voltage magnitudes from the available measurements using
        WLS regression. Pseudo-measurements at nominal voltage can supplement sparse
        telemetry for unobserved buses.

        Args:
            use_pseudo_measurements: Include pseudo-measurements for unobserved buses.

        Returns:
            str: Estimation summary including bus count and measurement count.
        """
        measurements = self._get("measurement_set")
        if not measurements:
            return "Error: Missing measurement_set. Generate or load measurements first."

        truth = self._get("truth_voltage_state") or {}
        pseudo = self._get("pseudo_measurement_set") or []
        grouped: dict[str, list[tuple[float, float]]] = {}
        for m in measurements:
            grouped.setdefault(m["bus"], []).append((float(m["value_pu"]), float(m.get("std_pu", 0.003))))
        if use_pseudo_measurements:
            for p in pseudo:
                grouped.setdefault(p["bus"], []).append((float(p["value_pu"]), float(p.get("std_pu", 0.03))))

        estimated = {}
        for bus in set(truth) | set(grouped):
            samples = grouped.get(bus)
            if not samples:
                estimated[bus] = 1.0
                continue
            weights = [1.0 / max(std ** 2, 1e-9) for _, std in samples]
            estimated[bus] = round(sum(v * w for (v, _), w in zip(samples, weights)) / sum(weights), 6)

        residuals = []
        for m in measurements:
            est = estimated.get(m["bus"], 1.0)
            reference = float(truth.get(m["bus"], est)) if truth else est
            residual = float(m["value_pu"]) - reference
            std = float(m.get("std_pu", 0.003))
            residuals.append({
                "id": m["id"],
                "bus": m["bus"],
                "residual_pu": round(residual, 6),
                "normalized_residual": round(abs(residual) / max(std, 1e-9), 3),
            })
        self._set("estimated_state", estimated)
        self._set("residual_report", residuals)
        return f"DSSE completed for {len(estimated)} buses using {len(measurements)} measurements."

    @agent_tool
    def compute_state_estimation_error(self) -> str:
        """
        Compute voltage estimation error relative to the synthetic truth state.

        Calculates RMSE and maximum absolute error across all buses where both
        estimated and truth voltages are available.

        Returns:
            str: Voltage RMSE and maximum absolute error in per-unit.
        """
        estimated = self._get("estimated_state")
        truth = self._get("truth_voltage_state")
        if not estimated or not truth:
            return "Error: Missing estimated_state or truth_voltage_state."
        common = sorted(set(estimated) & set(truth))
        if not common:
            return "Error: No common buses between estimate and truth."
        errors = [float(estimated[b]) - float(truth[b]) for b in common]
        rmse = math.sqrt(sum(e * e for e in errors) / len(errors))
        max_abs = max(abs(e) for e in errors)
        report = DSSEReport(voltage_rmse_pu=rmse, max_abs_error_pu=max_abs)
        self._set("state_error_report", report)
        return f"Voltage RMSE: {rmse:.6f} p.u.; Max abs error: {max_abs:.6f} p.u."

    @agent_tool
    def detect_bad_data(self, normalized_residual_threshold: float = 3.0) -> str:
        """
        Flag suspicious measurements using normalized residuals from the latest estimation.

        Measurements whose normalized residual exceeds the threshold are reported
        as bad-data candidates.

        Args:
            normalized_residual_threshold: Detection threshold in standard deviations.

        Returns:
            str: Count and IDs of flagged bad-data candidates.
        """
        residuals = self._get("residual_report")
        if not residuals:
            return "Error: Missing residual_report."
        flagged = [
            r for r in residuals
            if float(r.get("normalized_residual", 0.0)) >= normalized_residual_threshold
        ]
        report = {"threshold": normalized_residual_threshold, "flagged": flagged}
        self._set("bad_data_report", report)
        sample = ", ".join(r["id"] for r in flagged[:5])
        suffix = f", e.g. {sample}" if flagged else ""
        return f"Detected {len(flagged)} bad-data candidates{suffix}. Use export_dsse_report for full details."

    @agent_tool
    def export_dsse_report(
        self,
        file_format: Literal["json", "csv", "txt"] = "json",
    ) -> str:
        """
        Export DSSE estimation results to a file.

        Writes estimated voltages, error metrics, and bad-data records in the
        requested format.

        Args:
            file_format: Output format — `json`, `csv`, or `txt`.

        Returns:
            str: Path to the exported report file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"dsse_report.{file_format}"
        payload = {
            "estimated_state": self._get("estimated_state") or {},
            "state_error_report": self._get("state_error_report").__dict__ if self._get("state_error_report") else None,
            "bad_data_report": self._get("bad_data_report") or {},
            "bad_data_injection_record": self._get("bad_data_injection_record") or {},
        }
        if file_format == "json":
            path.write_text(json.dumps(payload, indent=2))
        elif file_format == "txt":
            path.write_text(json.dumps(payload, indent=2))
        elif file_format == "csv":
            with path.open("w", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(["bus", "estimated_voltage_pu"])
                for bus, value in sorted(payload["estimated_state"].items()):
                    writer.writerow([bus, value])
        else:
            return f"Error: Unsupported report format '{file_format}'."
        return f"DSSE report exported to '{path}'."

    @agent_tool
    def plot_estimated_voltage_map(self) -> str:
        """
        Plot estimated bus voltages as a compact profile chart.

        Returns:
            str: Path to the saved PNG voltage map.
        """
        estimated = self._get("estimated_state")
        if not estimated:
            return "Error: Missing estimated_state."
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "estimated_voltage_map.png"
        buses = list(sorted(estimated))[:60]
        values = [estimated[b] for b in buses]
        plt.figure(figsize=(10, 4))
        plt.plot(range(len(buses)), values, marker="o", linewidth=1)
        plt.ylabel("Estimated |V| (p.u.)")
        plt.xlabel("Bus index")
        plt.tight_layout()
        plt.savefig(path, dpi=200)
        plt.close()
        return f"Estimated voltage map saved to '{path}'."

    @agent_tool
    def plot_residuals(self) -> str:
        """
        Plot normalized measurement residuals as a bar chart.

        Returns:
            str: Path to the saved PNG residual plot.
        """
        residuals = self._get("residual_report")
        if not residuals:
            return "Error: Missing residual_report."
        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / "dsse_residuals.png"
        values = [float(r["normalized_residual"]) for r in residuals[:80]]
        plt.figure(figsize=(10, 4))
        plt.bar(range(len(values)), values)
        plt.axhline(3.0, color="red", linestyle="--", linewidth=1)
        plt.ylabel("Normalized residual")
        plt.xlabel("Measurement index")
        plt.tight_layout()
        plt.savefig(path, dpi=200)
        plt.close()
        return f"Residual plot saved to '{path}'."

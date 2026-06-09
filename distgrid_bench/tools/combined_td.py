from __future__ import annotations

import csv
import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, Literal, Optional

from distgrid_bench.tools.decorators import agent_tool

from distgrid_bench.tools import tool_config as config
from distgrid_bench.tools.shared_registry import SharedRegistry


@dataclass
class TransmissionBus:
    bus_id: int
    name: str
    base_kv: float
    voltage_pu: float
    angle_deg: float = 0.0
    p_load_mw: float = 0.0
    q_load_mvar: float = 0.0


@dataclass
class TransmissionBranch:
    from_bus: int
    to_bus: int
    r_pu: float = 0.0
    x_pu: float = 0.0


@dataclass
class TransmissionNetwork:
    source_path: str
    buses: Dict[int, TransmissionBus]
    branches: list[TransmissionBranch] = field(default_factory=list)

    @property
    def total_load_mw(self) -> float:
        return sum(bus.p_load_mw for bus in self.buses.values())

    @property
    def total_load_mvar(self) -> float:
        return sum(bus.q_load_mvar for bus in self.buses.values())


@dataclass
class DistributionBus:
    name: str
    nominal_voltage_v: float
    voltage_pu: float = 1.0
    p_load_kw: float = 0.0
    q_load_kvar: float = 0.0
    phase: str = "A"

    @property
    def voltage_v(self) -> float:
        return self.voltage_pu * self.nominal_voltage_v


@dataclass
class DistributionNetwork:
    source_path: str
    buses: Dict[str, DistributionBus]
    source_bus: str

    @property
    def total_load_kw(self) -> float:
        return sum(bus.p_load_kw for bus in self.buses.values())

    @property
    def total_load_kvar(self) -> float:
        return sum(bus.q_load_kvar for bus in self.buses.values())


@dataclass
class CouplingPort:
    transmission_bus_id: int
    distribution_source_bus: str
    transmission_voltage_pu: float = 1.0
    distribution_voltage_pu: float = 1.0
    p_exchange_mw: float = 0.0
    q_exchange_mvar: float = 0.0


@dataclass
class CombinedTDResult:
    solved: bool
    solver_requested: str
    method: str
    tolerance: float
    max_iter: int
    analysis_basis: str
    message: str
    total_transmission_load_mw: float
    total_distribution_load_mw: float
    coupling_port: CouplingPort
    transmission_voltage_pu: Dict[int, float]
    distribution_voltage_pu: Dict[str, float]
    weak_locations: list[dict] = field(default_factory=list)


@dataclass
class CombinedTDNetwork:
    transmission: TransmissionNetwork
    distribution: DistributionNetwork
    coupling_port: CouplingPort
    voltage_limits: dict = field(
        default_factory=lambda: {
            "transmission_vmin_pu": 0.95,
            "transmission_vmax_pu": 1.05,
            "distribution_vmin_pu": 0.95,
            "distribution_vmax_pu": 1.05,
            "enforcement": "reporting_only",
        }
    )
    original_transmission_loads: Dict[int, tuple[float, float]] = field(default_factory=dict)
    original_distribution_loads: Dict[str, tuple[float, float]] = field(default_factory=dict)
    solved: bool = False
    result: Optional[CombinedTDResult] = None

    def __post_init__(self) -> None:
        if not self.original_transmission_loads:
            self.original_transmission_loads = {
                bus_id: (bus.p_load_mw, bus.q_load_mvar)
                for bus_id, bus in self.transmission.buses.items()
            }
        if not self.original_distribution_loads:
            self.original_distribution_loads = {
                name: (bus.p_load_kw, bus.q_load_kvar)
                for name, bus in self.distribution.buses.items()
            }


def _resolve_path(path_value: str | Path | None, default: Path) -> Path:
    if not path_value:
        return default
    path = Path(str(path_value).replace("//", "/")).expanduser()
    if not path.is_absolute():
        path = config.BASE_DIR / path
    return path


def _split_csv_line(line: str) -> list[str]:
    reader = csv.reader([line], skipinitialspace=True)
    return [part.strip().strip("'\"") for part in next(reader)]


def _parse_float(value: object, default: float = 0.0) -> float:
    try:
        text = str(value).strip().rstrip(";")
        return float(text)
    except (TypeError, ValueError):
        return default


def _embedded_ieee14(path: Path) -> TransmissionNetwork:
    loads = {
        2: (21.7, 12.7),
        3: (94.2, 19.0),
        4: (47.8, -3.9),
        5: (7.6, 1.6),
        6: (11.2, 7.5),
        9: (29.5, 16.6),
        10: (9.0, 5.8),
        11: (3.5, 1.8),
        12: (6.1, 1.6),
        13: (13.5, 5.8),
        14: (14.9, 5.0),
    }
    voltages = {
        1: 1.060,
        2: 1.045,
        3: 1.010,
        4: 1.019,
        5: 1.020,
        6: 1.070,
        7: 1.062,
        8: 1.090,
        9: 1.056,
        10: 1.051,
        11: 1.057,
        12: 1.055,
        13: 1.050,
        14: 1.036,
    }
    buses = {
        bus_id: TransmissionBus(
            bus_id=bus_id,
            name=f"IEEE14_BUS_{bus_id}",
            base_kv=69.0,
            voltage_pu=voltage,
            p_load_mw=loads.get(bus_id, (0.0, 0.0))[0],
            q_load_mvar=loads.get(bus_id, (0.0, 0.0))[1],
        )
        for bus_id, voltage in voltages.items()
    }
    branches = [
        TransmissionBranch(1, 2, 0.01938, 0.05917),
        TransmissionBranch(1, 5, 0.05403, 0.22304),
        TransmissionBranch(2, 3, 0.04699, 0.19797),
        TransmissionBranch(2, 4, 0.05811, 0.17632),
        TransmissionBranch(2, 5, 0.05695, 0.17388),
        TransmissionBranch(3, 4, 0.06701, 0.17103),
        TransmissionBranch(4, 5, 0.01335, 0.04211),
        TransmissionBranch(4, 7, 0.0, 0.20912),
        TransmissionBranch(4, 9, 0.0, 0.55618),
        TransmissionBranch(5, 6, 0.0, 0.25202),
        TransmissionBranch(6, 11, 0.09498, 0.19890),
        TransmissionBranch(6, 12, 0.12291, 0.25581),
        TransmissionBranch(6, 13, 0.06615, 0.13027),
        TransmissionBranch(7, 8, 0.0, 0.17615),
        TransmissionBranch(7, 9, 0.0, 0.11001),
        TransmissionBranch(9, 10, 0.03181, 0.08450),
        TransmissionBranch(9, 14, 0.12711, 0.27038),
        TransmissionBranch(10, 11, 0.08205, 0.19207),
        TransmissionBranch(12, 13, 0.22092, 0.19988),
        TransmissionBranch(13, 14, 0.17093, 0.34802),
    ]
    return TransmissionNetwork(source_path=str(path), buses=buses, branches=branches)


def _parse_custom_raw(path: Path, text: str) -> Optional[TransmissionNetwork]:
    current = None
    buses: Dict[int, TransmissionBus] = {}
    branches: list[TransmissionBranch] = []
    loads: Dict[int, tuple[float, float]] = {}

    for raw_line in text.splitlines():
        line = raw_line.split("/", 1)[0].strip()
        if not line:
            continue
        marker = line.upper()
        if marker == "BEGIN BUS":
            current = "bus"
            continue
        if marker == "BEGIN LOAD":
            current = "load"
            continue
        if marker == "BEGIN BRANCH":
            current = "branch"
            continue
        if marker.startswith("END "):
            current = None
            continue
        if current is None:
            continue

        parts = _split_csv_line(line)
        if current == "bus" and len(parts) >= 5:
            bus_id = int(parts[0])
            buses[bus_id] = TransmissionBus(
                bus_id=bus_id,
                name=parts[1],
                voltage_pu=_parse_float(parts[2], 1.0),
                angle_deg=_parse_float(parts[3]),
                base_kv=_parse_float(parts[4], 69.0),
            )
        elif current == "load" and len(parts) >= 3:
            loads[int(parts[0])] = (_parse_float(parts[1]), _parse_float(parts[2]))
        elif current == "branch" and len(parts) >= 4:
            branches.append(
                TransmissionBranch(
                    from_bus=int(parts[0]),
                    to_bus=int(parts[1]),
                    r_pu=_parse_float(parts[2]),
                    x_pu=_parse_float(parts[3]),
                )
            )

    if not buses:
        return None
    for bus_id, (p_load, q_load) in loads.items():
        if bus_id in buses:
            buses[bus_id].p_load_mw = p_load
            buses[bus_id].q_load_mvar = q_load
    return TransmissionNetwork(source_path=str(path), buses=buses, branches=branches)


def _parse_psse_raw(path: Path, text: str) -> Optional[TransmissionNetwork]:
    buses: Dict[int, TransmissionBus] = {}
    branches: list[TransmissionBranch] = []
    section = "bus"

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("@") or line.startswith("0 /"):
            upper = line.upper()
            if "END OF BUS DATA" in upper:
                section = "load"
            elif "END OF LOAD DATA" in upper:
                section = "branch"
            elif "END OF BRANCH DATA" in upper:
                section = "done"
            continue
        if section == "done":
            break
        parts = _split_csv_line(line)
        if not parts or not parts[0].lstrip("-").isdigit():
            continue
        if section == "bus" and len(parts) >= 9:
            bus_id = int(parts[0])
            buses[bus_id] = TransmissionBus(
                bus_id=bus_id,
                name=parts[1] or f"BUS_{bus_id}",
                base_kv=_parse_float(parts[2], 69.0),
                voltage_pu=_parse_float(parts[7], 1.0),
                angle_deg=_parse_float(parts[8]),
            )
        elif section == "load" and len(parts) >= 7:
            bus_id = int(parts[0])
            if bus_id in buses:
                buses[bus_id].p_load_mw += _parse_float(parts[5])
                buses[bus_id].q_load_mvar += _parse_float(parts[6])
        elif section == "branch" and len(parts) >= 5:
            branches.append(
                TransmissionBranch(
                    from_bus=int(parts[0]),
                    to_bus=int(parts[1]),
                    r_pu=_parse_float(parts[3]),
                    x_pu=_parse_float(parts[4]),
                )
            )

    if not buses:
        return None
    return TransmissionNetwork(source_path=str(path), buses=buses, branches=branches)


def parse_transmission_raw(path: Path) -> TransmissionNetwork:
    if not path.exists():
        if path.name == "IEEE-14_prior_solution.RAW":
            return _embedded_ieee14(path)
        raise FileNotFoundError(f"RAW file not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")
    parsed = _parse_custom_raw(path, text) or _parse_psse_raw(path, text)
    if parsed is None:
        raise ValueError(f"Could not parse transmission RAW file: {path}")
    return parsed


def _embedded_four_bus(path: Path) -> DistributionNetwork:
    buses = {
        "sourcebus": DistributionBus("sourcebus", 2400.0, 1.0, 0.0, 0.0, "ABC"),
        "loadbus_1": DistributionBus("loadbus_1", 2400.0, 0.992, 180.0, 60.0, "A"),
        "loadbus_2": DistributionBus("loadbus_2", 2400.0, 0.986, 140.0, 45.0, "B"),
        "loadbus_3": DistributionBus("loadbus_3", 2400.0, 0.979, 110.0, 30.0, "C"),
    }
    return DistributionNetwork(source_path=str(path), buses=buses, source_bus="sourcebus")


def _parse_complex_power_kw(value: str) -> tuple[float, float]:
    text = str(value).strip().strip(";").replace(" ", "")
    if not text:
        return 0.0, 0.0
    text = text.replace("j", "J")
    try:
        value_c = complex(text)
        return value_c.real / 1000.0, value_c.imag / 1000.0
    except ValueError:
        return _parse_float(text) / 1000.0, 0.0


def parse_distribution_glm(path: Path) -> DistributionNetwork:
    if not path.exists():
        if path.name == "node.glm":
            return _embedded_four_bus(path)
        raise FileNotFoundError(f"GLM file not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")
    object_blocks = re.findall(r"object\s+(\w+)\s*\{(.*?)\}", text, flags=re.IGNORECASE | re.DOTALL)
    buses: Dict[str, DistributionBus] = {}
    load_accumulator: Dict[str, tuple[float, float]] = {}
    source_bus: Optional[str] = None

    for object_type, body in object_blocks:
        fields = dict(
            (match.group(1), match.group(2).strip().strip("'\""))
            for match in re.finditer(r"(\w+)\s+([^;\n]+);", body)
        )
        name = fields.get("name")
        if not name:
            continue
        nominal_voltage = _parse_float(fields.get("nominal_voltage"), 2400.0)
        bustype = fields.get("bustype", "").upper()
        if object_type.lower() in {"node", "meter", "triplex_node", "triplex_meter"}:
            if name not in buses:
                buses[name] = DistributionBus(
                    name=name,
                    nominal_voltage_v=nominal_voltage,
                    voltage_pu=1.0,
                    phase=fields.get("phases", "A"),
                )
            if "SWING" in bustype or source_bus is None:
                source_bus = name
        if object_type.lower() in {"load", "triplex_load"}:
            load_bus = name
            p_kw = q_kvar = 0.0
            for key, value in fields.items():
                if key.startswith("constant_power"):
                    p_part, q_part = _parse_complex_power_kw(value)
                    p_kw += p_part
                    q_kvar += q_part
            if load_bus not in buses:
                buses[load_bus] = DistributionBus(
                    name=load_bus,
                    nominal_voltage_v=nominal_voltage,
                    voltage_pu=1.0,
                    phase=fields.get("phases", "A"),
                )
            old_p, old_q = load_accumulator.get(load_bus, (0.0, 0.0))
            load_accumulator[load_bus] = (old_p + p_kw, old_q + q_kvar)

    for bus_name, (p_load, q_load) in load_accumulator.items():
        buses[bus_name].p_load_kw = p_load
        buses[bus_name].q_load_kvar = q_load

    if not buses:
        raise ValueError(f"Could not parse distribution GLM buses from: {path}")
    source = source_bus or next(iter(buses))
    return DistributionNetwork(source_path=str(path), buses=buses, source_bus=source)


def distribution_from_dx_model(
    model: object,
    source_path: str,
    source_bus: Optional[str] = None,
) -> DistributionNetwork:
    buses: Dict[str, DistributionBus] = {}

    for bus in getattr(model, "buses", []):
        name = str(getattr(bus, "NodeName", "") or "").strip()
        if not name or name.lower() == "gnd":
            continue

        nominal_voltage = float(getattr(bus, "V_Nominal", 1.0) or 1.0)
        vr = float(getattr(bus, "Vr", nominal_voltage) or 0.0)
        vi = float(getattr(bus, "Vi", 0.0) or 0.0)
        voltage_pu = ((vr**2 + vi**2) ** 0.5) / nominal_voltage if nominal_voltage else 1.0
        phase = str(getattr(bus, "NodePhase", "") or "")

        if name not in buses:
            buses[name] = DistributionBus(
                name=name,
                nominal_voltage_v=nominal_voltage,
                voltage_pu=voltage_pu,
                phase=phase,
            )
        else:
            existing = buses[name]
            existing.voltage_pu = min(existing.voltage_pu, voltage_pu)
            if phase and phase not in existing.phase:
                existing.phase = f"{existing.phase}{phase}"

    for load in getattr(model, "loads", []):
        load_bus = getattr(load, "from_bus", None)
        name = str(getattr(load_bus, "NodeName", "") or "").strip()
        if not name:
            continue
        if name not in buses:
            nominal_voltage = float(getattr(load_bus, "V_Nominal", 1.0) or 1.0)
            buses[name] = DistributionBus(name=name, nominal_voltage_v=nominal_voltage)
        buses[name].p_load_kw += float(getattr(load, "P", 0.0) or 0.0) / 1000.0
        buses[name].q_load_kvar += float(getattr(load, "Q", 0.0) or 0.0) / 1000.0

    if not buses:
        raise ValueError("Active distribution model has no usable buses.")

    inferred_source = source_bus
    if not inferred_source:
        slack = getattr(model, "slack", []) or []
        if slack:
            inferred_source = str(getattr(getattr(slack[0], "bus", None), "NodeName", "") or "").strip()
    if not inferred_source or inferred_source not in buses:
        inferred_source = next(iter(buses))

    return DistributionNetwork(source_path=source_path, buses=buses, source_bus=inferred_source)


def _violation_severity(voltage_pu: float, vmin: float, vmax: float) -> float:
    if voltage_pu < vmin:
        return vmin - voltage_pu
    if voltage_pu > vmax:
        return voltage_pu - vmax
    return 0.0


def _as_serializable_result(result: CombinedTDResult) -> dict:
    data = asdict(result)
    data["coupling_port"] = asdict(result.coupling_port)
    return data


class CombinedTDTools:
    def __init__(self, registry: SharedRegistry):
        self.registry = registry
        self.output_dir = config.EXECUTION_OUTPUT_DIR / "combined_td"

    def _combined(self) -> Optional[CombinedTDNetwork]:
        model = self.registry.get("combined_td:active")
        return model if isinstance(model, CombinedTDNetwork) else None

    @agent_tool
    def load_transmission_network(self, path_raw: str = "") -> str:
        """
        Load the transmission network from a RAW file.

        Args:
            path_raw: Optional RAW file path. Use "" unless the user provides
                a specific RAW path. The default loads the local IEEE-14
                benchmark fixture as the Vermont transmission surrogate.

        Returns:
            str: Status showing the number of buses, branches, and total load.
        """
        try:
            path = _resolve_path(path_raw, config.COMBINED_TD_DEFAULT_RAW)
            prompt = str(self.registry.get("last_user_prompt") or "").lower()
            model_invented_path = (
                bool(path_raw)
                and not path.exists()
                and ".raw" not in prompt
            )
            if model_invented_path:
                path = config.COMBINED_TD_DEFAULT_RAW

            network = parse_transmission_raw(path)
            self.registry.set("transmission:active", network)
            return (
                f"{config.COMBINED_TD_TRANSMISSION_LABEL} loaded from '{path}'. "
                f"Buses: {len(network.buses)} | Branches: {len(network.branches)} | "
                f"Total load: {network.total_load_mw:.3f} MW / {network.total_load_mvar:.3f} MVAr."
            )
        except Exception as exc:
            return f"Error: {exc}"

    @agent_tool
    def summarize_transmission_network(self) -> str:
        """
        Summarize the active transmission network.

        This tool does not create a combined T&D model. Use it for lightweight
        upstream transmission context such as bus count, branch count, total
        load, and voltage range.

        Returns:
            str: Standalone transmission summary with load and voltage range.
        """
        network = self.registry.get("transmission:active")
        if not isinstance(network, TransmissionNetwork):
            return "Error: Required transmission state is missing."

        voltages = [bus.voltage_pu for bus in network.buses.values()]
        min_v = min(voltages) if voltages else 0.0
        max_v = max(voltages) if voltages else 0.0
        return (
            "--- Transmission Network Summary ---\n"
            f"System: {config.COMBINED_TD_TRANSMISSION_LABEL}\n"
            f"Source: {network.source_path}\n"
            f"Buses: {len(network.buses)} | Branches: {len(network.branches)}\n"
            f"Total load: {network.total_load_mw:.3f} MW / {network.total_load_mvar:.3f} MVAr\n"
            f"Voltage range: {min_v:.4f}-{max_v:.4f} p.u."
        )

    @agent_tool
    def get_transmission_bus_voltage(self, bus_id: int) -> str:
        """
        Report voltage magnitude and angle for one transmission bus.

        Args:
            bus_id: Transmission bus id to inspect.

        Returns:
            str: Bus name, base kV, voltage p.u., angle, and load.
        """
        network = self.registry.get("transmission:active")
        if not isinstance(network, TransmissionNetwork):
            return "Error: Required transmission state is missing."
        if bus_id not in network.buses:
            sample = sorted(str(b) for b in network.buses)[:5]
            return f"Error: Transmission bus {bus_id} not found. {len(network.buses)} buses available, e.g. {', '.join(sample)}."

        bus = network.buses[bus_id]
        return (
            f"Transmission bus {bus.bus_id} ({bus.name}) | "
            f"Base: {bus.base_kv:.3f} kV | V: {bus.voltage_pu:.4f} p.u. | "
            f"Angle: {bus.angle_deg:.3f} deg | "
            f"Load: {bus.p_load_mw:.3f} MW / {bus.q_load_mvar:.3f} MVAr"
        )

    @agent_tool
    def list_transmission_voltage_violations(
        self,
        vmin_pu: float = 0.95,
        vmax_pu: float = 1.05,
        top_k: int = 50,
    ) -> str:
        """
        List upstream transmission buses outside a voltage range.

        Args:
            vmin_pu: Minimum acceptable transmission voltage in p.u.
            vmax_pu: Maximum acceptable transmission voltage in p.u.
            top_k: Maximum number of highest-severity violations to list.

        Returns:
            str: Violation list or a clean-status message.
        """
        network = self.registry.get("transmission:active")
        if not isinstance(network, TransmissionNetwork):
            return "Error: Required transmission state is missing."
        if vmin_pu >= vmax_pu:
            return "Error: vmin_pu must be lower than vmax_pu."

        violations = [
            bus
            for bus in network.buses.values()
            if bus.voltage_pu < vmin_pu or bus.voltage_pu > vmax_pu
        ]
        if not violations:
            return (
                f"No transmission voltage violations found for "
                f"{vmin_pu:.3f}-{vmax_pu:.3f} p.u."
            )

        top_k = max(1, min(int(top_k), 200))
        ranked = sorted(
            violations,
            key=lambda item: (-_violation_severity(item.voltage_pu, vmin_pu, vmax_pu), item.bus_id),
        )
        shown = ranked[:top_k]
        lines = [
            f"Transmission voltage violations found: {len(violations)} "
            f"outside {vmin_pu:.3f}-{vmax_pu:.3f} p.u.",
            f"Showing top {len(shown)} by voltage-limit severity.",
        ]
        for bus in shown:
            lines.append(
                f"Bus {bus.bus_id} ({bus.name}) | V={bus.voltage_pu:.4f} p.u. | "
                f"severity={_violation_severity(bus.voltage_pu, vmin_pu, vmax_pu):.6f}"
            )
        if len(violations) > len(shown):
            lines.append(
                f"{len(violations) - len(shown)} additional violations omitted; "
                "increase top_k only if a longer listing is required."
            )
        return "\n".join(lines)

    @agent_tool
    def prepare_distribution_for_coupling(
        self,
        feeder: Literal["south_hero", "rochester", "stowe", "glover", "active"] = "active",
        path_glm: str = "",
    ) -> str:
        """
        Prepare a distribution network for combined T&D coupling.

        For named feeders, this converts the already-loaded DxNetworkModel from
        network:active into the combined T&D distribution representation. Load the
        feeder first with NetworkLoader.load_distribution_network. If an explicit GLM path is
        provided, this parses that GLM directly.

        Args:
            feeder: Distribution source. Use 'active' for the current network:active
                model, or one of the configured feeder names.
            path_glm: Optional explicit GLM file path. If provided, it is parsed
                directly and feeder is ignored.

        Returns:
            str: Status showing the number of distribution buses, source bus,
            and total distribution load.
        """
        try:
            if path_glm:
                path = _resolve_path(path_glm, config.COMBINED_TD_DEFAULT_GLM)
                network = parse_distribution_glm(path)
                source_label = str(path)
            else:
                active_model = self.registry.get("network:active")
                if active_model is None:
                    return "Error: Required distribution state is missing."

                source_label = f"network:active/{feeder}"
                network = distribution_from_dx_model(active_model, source_label)

            self.registry.set("distribution:active", network)
            return (
                f"Distribution network loaded from '{source_label}'. "
                f"Buses: {len(network.buses)} | Source bus: {network.source_bus} | "
                f"Total load: {network.total_load_kw:.3f} kW / {network.total_load_kvar:.3f} kVAr."
            )
        except Exception as exc:
            return f"Error: {exc}"

    @agent_tool
    def create_combined_td_model(
        self,
        transmission_poi_bus: int = 14,
        distribution_source_bus: Optional[str] = None,
    ) -> str:
        """
        Couple the active Vermont transmission/subtransmission system and one
        active distribution feeder into a combined T&D model.

        Couples the active transmission and distribution networks into a combined T&D model.

        Args:
            transmission_poi_bus: Transmission point-of-interconnection bus id.
            distribution_source_bus: Optional distribution source bus name. If
                omitted, the active distribution source bus is used.

        Returns:
            str: Creation summary with registry keys and coupling endpoint.
        """
        try:
            transmission = self.registry.get("transmission:active")
            if not isinstance(transmission, TransmissionNetwork):
                return "Error: Required transmission state is missing."

            distribution = self.registry.get("distribution:active")
            if not isinstance(distribution, DistributionNetwork):
                return "Error: Required distribution state is missing."

            if transmission_poi_bus not in transmission.buses:
                sample = sorted(str(b) for b in transmission.buses)[:5]
                return f"Error: Transmission POI bus {transmission_poi_bus} not found. {len(transmission.buses)} buses available, e.g. {', '.join(sample)}."
            if distribution_source_bus:
                if distribution_source_bus not in distribution.buses:
                    sample = sorted(distribution.buses)[:5]
                    return f"Error: Distribution source bus '{distribution_source_bus}' not found. {len(distribution.buses)} buses available, e.g. {', '.join(sample)}."
                distribution.source_bus = distribution_source_bus

            poi_voltage = transmission.buses[transmission_poi_bus].voltage_pu
            distribution.buses[distribution.source_bus].voltage_pu = poi_voltage
            port = CouplingPort(
                transmission_bus_id=transmission_poi_bus,
                distribution_source_bus=distribution.source_bus,
                transmission_voltage_pu=poi_voltage,
                distribution_voltage_pu=poi_voltage,
                p_exchange_mw=distribution.total_load_kw / 1000.0,
                q_exchange_mvar=distribution.total_load_kvar / 1000.0,
            )
            combined = CombinedTDNetwork(transmission, distribution, port)
            self.registry.set("combined_td:active", combined)
            self.registry.set("combined_td:result", None)
            return (
                "Combined T&D model created and stored as 'combined_td:active'. "
                f"Transmission system: {config.COMBINED_TD_TRANSMISSION_LABEL} | "
                f"Transmission buses: {len(transmission.buses)} | Distribution buses: {len(distribution.buses)} | "
                f"POI: transmission bus {transmission_poi_bus} -> distribution bus '{distribution.source_bus}'."
            )
        except Exception as exc:
            return f"Error: {exc}"

    @agent_tool
    def run_combined_td_powerflow(
        self,
        solver: str = "ipopt",
        tolerance: float = 1e-6,
        max_iter: int = 1000,
    ) -> str:
        """
        Run the coupled benchmark T&D power-flow approximation.

        The current implementation is a reduced deterministic coupled solver,
        not the old full IPOPT model. The requested solver settings are recorded
        for traceability. Failed runs do not update solved state or voltages.

        Args:
            solver: Requested solver name, usually 'ipopt'.
            tolerance: Positive convergence tolerance.
            max_iter: Positive maximum iteration count.

        Returns:
            str: Solve status, analysis basis, and POI exchange summary.
        """
        combined = self._combined()
        if not combined:
            return "Error: Required combined T&D state is missing."
        tolerance = max(tolerance, 1e-10)
        if tolerance <= 0 or max_iter <= 0:
            return "Error: tolerance and max_iter must both be positive. Combined T&D state was not updated."

        try:
            t_load = combined.transmission.total_load_mw
            d_load_mw = combined.distribution.total_load_kw / 1000.0
            d_load_mvar = combined.distribution.total_load_kvar / 1000.0
            poi_bus = combined.transmission.buses[combined.coupling_port.transmission_bus_id]
            poi_base = poi_bus.voltage_pu
            poi_drop = min(0.12, 0.0015 * d_load_mw + 0.00008 * t_load)
            poi_voltage = max(0.80, poi_base - poi_drop)

            for bus in combined.transmission.buses.values():
                local_load = bus.p_load_mw + (d_load_mw if bus.bus_id == poi_bus.bus_id else 0.0)
                voltage_drop = min(0.10, 0.00035 * local_load)
                bus.voltage_pu = max(0.80, bus.voltage_pu - voltage_drop)

            combined.transmission.buses[poi_bus.bus_id].voltage_pu = poi_voltage
            combined.coupling_port.transmission_voltage_pu = poi_voltage
            combined.coupling_port.distribution_voltage_pu = poi_voltage
            combined.coupling_port.p_exchange_mw = d_load_mw
            combined.coupling_port.q_exchange_mvar = d_load_mvar

            ordered_distribution = list(combined.distribution.buses.values())
            cumulative_kw = 0.0
            for idx, bus in enumerate(ordered_distribution):
                cumulative_kw += bus.p_load_kw
                if bus.name == combined.distribution.source_bus:
                    bus.voltage_pu = poi_voltage
                    continue
                distance_drop = 0.0035 * idx
                loading_drop = min(0.08, 0.000035 * cumulative_kw)
                bus.voltage_pu = max(0.75, poi_voltage - distance_drop - loading_drop)

            weak_locations = self._rank_weak_locations(combined)
            result = CombinedTDResult(
                solved=True,
                solver_requested=solver,
                method="reduced_coupled_powerflow",
                tolerance=tolerance,
                max_iter=max_iter,
                analysis_basis="powerflow_voltage_update",
                message=(
                    "Reduced coupled power flow completed. Solver request was recorded; "
                    "no external optimizer was invoked in this local benchmark path."
                ),
                total_transmission_load_mw=t_load,
                total_distribution_load_mw=d_load_mw,
                coupling_port=combined.coupling_port,
                transmission_voltage_pu={
                    bus_id: bus.voltage_pu for bus_id, bus in combined.transmission.buses.items()
                },
                distribution_voltage_pu={
                    name: bus.voltage_pu for name, bus in combined.distribution.buses.items()
                },
                weak_locations=weak_locations,
            )
            combined.solved = True
            combined.result = result
            self.registry.set("combined_td:result", result)
            return (
                "Combined T&D power flow completed with method='reduced_coupled_powerflow'. "
                f"Analysis basis: {result.analysis_basis}. "
                f"POI voltage: {combined.coupling_port.transmission_voltage_pu:.4f} p.u. | "
                f"P/Q exchange: {d_load_mw:.4f} MW / {d_load_mvar:.4f} MVAr."
            )
        except Exception as exc:
            combined.solved = False
            combined.result = None
            self.registry.set("combined_td:result", None)
            return f"Error: Combined T&D solve failed and state was not updated: {exc}"

    @agent_tool
    def scale_combined_td_loads(
        self,
        system: Literal["transmission", "distribution", "both"],
        multiplier: float,
    ) -> str:
        """
        Scale transmission and/or distribution loads.

        Args:
            system: Which side to scale: transmission, distribution, or both.
            multiplier: Non-negative load multiplier.

        Returns:
            str: Load totals after scaling. Solved state is cleared.
        """
        combined = self._combined()
        if not combined:
            return "Error: Required combined T&D state is missing."
        if multiplier < 0:
            return "Error: multiplier must be non-negative."

        if system in {"transmission", "both"}:
            for bus_id, (p_load, q_load) in combined.original_transmission_loads.items():
                combined.transmission.buses[bus_id].p_load_mw = p_load * multiplier
                combined.transmission.buses[bus_id].q_load_mvar = q_load * multiplier
        if system in {"distribution", "both"}:
            for name, (p_load, q_load) in combined.original_distribution_loads.items():
                combined.distribution.buses[name].p_load_kw = p_load * multiplier
                combined.distribution.buses[name].q_load_kvar = q_load * multiplier

        combined.solved = False
        combined.result = None
        self.registry.set("combined_td:result", None)
        return (
            f"Scaled {system} loads by {multiplier:.3f}. "
            f"Transmission load: {combined.transmission.total_load_mw:.3f} MW | "
            f"Distribution load: {combined.distribution.total_load_kw:.3f} kW. "
            "Solved state cleared; rerun run_combined_td_powerflow."
        )

    @agent_tool
    def reset_combined_td_loads(self) -> str:
        """
        Reset combined T&D loads to their baselines.

        Returns:
            str: Reset confirmation and baseline load totals.
        """
        combined = self._combined()
        if not combined:
            return "Error: Required combined T&D state is missing."

        for bus_id, (p_load, q_load) in combined.original_transmission_loads.items():
            combined.transmission.buses[bus_id].p_load_mw = p_load
            combined.transmission.buses[bus_id].q_load_mvar = q_load
        for name, (p_load, q_load) in combined.original_distribution_loads.items():
            combined.distribution.buses[name].p_load_kw = p_load
            combined.distribution.buses[name].q_load_kvar = q_load

        combined.solved = False
        combined.result = None
        self.registry.set("combined_td:result", None)
        return (
            "Combined T&D loads reset to baseline. "
            f"Transmission load: {combined.transmission.total_load_mw:.3f} MW | "
            f"Distribution load: {combined.distribution.total_load_kw:.3f} kW. "
            "Solved state cleared."
        )

    @agent_tool
    def set_combined_td_voltage_limits(
        self,
        transmission_vmin_pu: float = 0.95,
        transmission_vmax_pu: float = 1.05,
        distribution_vmin_pu: float = 0.95,
        distribution_vmax_pu: float = 1.05,
    ) -> str:
        """
        Set voltage limits for combined T&D reporting.

        These reduced benchmark limits are reporting-only. They are not enforced
        as optimization constraints unless a future full constrained solver is attached.

        Args:
            transmission_vmin_pu: Minimum transmission voltage in p.u.
            transmission_vmax_pu: Maximum transmission voltage in p.u.
            distribution_vmin_pu: Minimum distribution voltage in normalized p.u.
            distribution_vmax_pu: Maximum distribution voltage in normalized p.u.

        Returns:
            str: Configured limits and enforcement basis.
        """
        combined = self._combined()
        if not combined:
            return "Error: Required combined T&D state is missing."
        if transmission_vmin_pu >= transmission_vmax_pu or distribution_vmin_pu >= distribution_vmax_pu:
            return "Error: Minimum voltage limits must be lower than maximum voltage limits."

        combined.voltage_limits = {
            "transmission_vmin_pu": transmission_vmin_pu,
            "transmission_vmax_pu": transmission_vmax_pu,
            "distribution_vmin_pu": distribution_vmin_pu,
            "distribution_vmax_pu": distribution_vmax_pu,
            "enforcement": "reporting_only",
        }
        return (
            "Combined T&D voltage limits updated for reporting-only checks. "
            f"Transmission: {transmission_vmin_pu:.3f}-{transmission_vmax_pu:.3f} p.u. | "
            f"Distribution normalized: {distribution_vmin_pu:.3f}-{distribution_vmax_pu:.3f} p.u."
        )

    @agent_tool
    def run_combined_td_infeasibility(
        self,
        norm: Literal["l1", "l2"] = "l2",
        top_k: int = 10,
    ) -> str:
        """
        Run reduced combined T&D voltage-deficit analysis.

        This is not a true slack-current IPOPT infeasibility model. It ranks
        post-solve voltage-limit deficits and records
        analysis_basis='post_solve_voltage_deficit'.

        Args:
            norm: Severity aggregation norm, either l1 or l2.
            top_k: Number of weak locations to show.

        Returns:
            str: Severity score and weak locations.
        """
        combined = self._combined()
        if not combined:
            return "Error: Required combined T&D state is missing."
        if not combined.solved or not combined.result:
            return "Error: Required power flow results are missing."

        weak_locations = self._rank_weak_locations(combined)
        severities = [float(item["severity_pu"]) for item in weak_locations]
        if norm == "l1":
            score = sum(severities)
        else:
            score = math.sqrt(sum(value * value for value in severities))

        combined.result.analysis_basis = "post_solve_voltage_deficit"
        combined.result.weak_locations = weak_locations
        self.registry.set("combined_td:result", combined.result)

        lines = [
            f"Combined T&D {norm.upper()} voltage-deficit analysis complete.",
            "Analysis basis: post_solve_voltage_deficit (not true infeasibility-source variables).",
            f"Severity score: {score:.6f} p.u.",
            f"Top {min(top_k, len(weak_locations))} weak locations:",
        ]
        for idx, item in enumerate(weak_locations[:top_k], start=1):
            lines.append(
                f"{idx}. {item['system']} {item['id']} | V={item['voltage_pu']:.4f} p.u. | "
                f"severity={item['severity_pu']:.6f}"
            )
        return "\n".join(lines)

    @agent_tool
    def summarize_combined_td_results(self) -> str:
        """
        Summarize the latest combined T&D state and solve result.

        Returns:
            str: Transmission load, distribution load, POI voltage/exchange,
            voltage basis, and solved status.
        """
        combined = self._combined()
        if not combined:
            return "Error: Required combined T&D state is missing."

        status = "solved" if combined.solved and combined.result else "not solved"
        basis = combined.result.analysis_basis if combined.result else "not_available"
        return (
            "--- Combined T&D Summary ---\n"
            f"Status: {status}\n"
            f"Transmission system: {config.COMBINED_TD_TRANSMISSION_LABEL}\n"
            f"Transmission source: {combined.transmission.source_path}\n"
            f"Distribution source: {combined.distribution.source_path}\n"
            f"Transmission buses: {len(combined.transmission.buses)} | "
            f"Distribution buses: {len(combined.distribution.buses)}\n"
            f"Transmission load: {combined.transmission.total_load_mw:.3f} MW / "
            f"{combined.transmission.total_load_mvar:.3f} MVAr\n"
            f"Distribution load: {combined.distribution.total_load_kw:.3f} kW / "
            f"{combined.distribution.total_load_kvar:.3f} kVAr\n"
            f"POI bus: {combined.coupling_port.transmission_bus_id} -> "
            f"{combined.coupling_port.distribution_source_bus}\n"
            f"POI voltage: {combined.coupling_port.transmission_voltage_pu:.4f} p.u.\n"
            f"P/Q exchange: {combined.coupling_port.p_exchange_mw:.4f} MW / "
            f"{combined.coupling_port.q_exchange_mvar:.4f} MVAr\n"
            f"Voltage reporting basis: transmission already p.u.; distribution normalized by nominal voltage.\n"
            f"Analysis basis: {basis}"
        )

    @agent_tool
    def summarize_coupling_port(self) -> str:
        """
        Report the transmission-distribution coupling port values.

        Returns:
            str: POI endpoints, voltage, and real/reactive exchange.
        """
        combined = self._combined()
        if not combined:
            return "Error: Required combined T&D state is missing."
        port = combined.coupling_port
        return (
            "--- Combined T&D Coupling Port ---\n"
            f"Transmission POI bus: {port.transmission_bus_id}\n"
            f"Distribution source bus: {port.distribution_source_bus}\n"
            f"Transmission voltage: {port.transmission_voltage_pu:.4f} p.u.\n"
            f"Distribution source voltage: {port.distribution_voltage_pu:.4f} p.u. "
            "(normalized by V_Nominal, not raw volts)\n"
            f"P exchange: {port.p_exchange_mw:.4f} MW\n"
            f"Q exchange: {port.q_exchange_mvar:.4f} MVAr"
        )

    @agent_tool
    def list_combined_td_voltage_violations(self, top_k: int = 10) -> str:
        """
        List transmission and distribution voltage violations.

        Distribution voltages are reported in normalized p.u. using each bus
        nominal voltage; raw distribution volts are not reported as p.u.

        Args:
            top_k: Maximum number of highest-severity violations to list.

        Returns:
            str: Violation list or a clean-status message.
        """
        combined = self._combined()
        if not combined:
            return "Error: Required combined T&D state is missing."

        violations = self._voltage_violations(combined)
        if not violations:
            return (
                "No combined T&D voltage violations found. "
                "Distribution voltages were normalized by nominal voltage."
            )

        top_k = max(1, min(int(top_k), 50))
        ranked = sorted(
            violations,
            key=lambda item: (-float(item["severity_pu"]), str(item["system"]), str(item["id"])),
        )
        shown = ranked[:top_k]
        lines = [
            f"Combined T&D voltage violations found: {len(violations)}",
            f"Showing top {len(shown)} by voltage-limit severity.",
        ]
        for item in shown:
            lines.append(
                f"{item['system']} {item['id']} | V={item['voltage_pu']:.4f} p.u. | "
                f"limit={item['vmin_pu']:.3f}-{item['vmax_pu']:.3f} p.u. | "
                f"severity={item['severity_pu']:.6f}"
            )
        if len(violations) > len(shown):
            lines.append(
                f"{len(violations) - len(shown)} additional violations omitted; "
                "increase top_k only if a longer listing is required."
            )
        return "\n".join(lines)

    @agent_tool
    def list_combined_td_weak_locations(self, top_k: int = 10) -> str:
        """
        Rank weak combined T&D locations by voltage-limit deficit.

        Args:
            top_k: Number of locations to list.

        Returns:
            str: Sorted weak-location list across transmission and distribution.
        """
        combined = self._combined()
        if not combined:
            return "Error: Required combined T&D state is missing."

        top_k = max(1, min(int(top_k), 200))
        weak_locations = self._rank_weak_locations(combined)
        if not weak_locations:
            return "No weak locations found under the current reporting limits."

        lines = [f"--- Top {min(top_k, len(weak_locations))} Combined T&D Weak Locations ---"]
        for idx, item in enumerate(weak_locations[:top_k], start=1):
            lines.append(
                f"{idx}. {item['system']} {item['id']} | V={item['voltage_pu']:.4f} p.u. | "
                f"severity={item['severity_pu']:.6f}"
            )
        return "\n".join(lines)

    @agent_tool
    def export_combined_td_results(
        self,
        export_type: Literal["summary", "voltages", "violations", "weak_locations"],
        file_format: Literal["csv", "json"],
    ) -> str:
        """
        Export combined T&D results to CSV or JSON.

        Args:
            export_type: summary, voltages, violations, or weak_locations.
            file_format: csv or json.

        Returns:
            str: Output file path and row count.
        """
        combined = self._combined()
        if not combined:
            return "Error: No combined T&D model is active."

        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"{export_type}.{file_format}"

        if export_type == "summary":
            payload = {
                "status": "solved" if combined.solved else "not_solved",
                "transmission_source": combined.transmission.source_path,
                "distribution_source": combined.distribution.source_path,
                "transmission_load_mw": combined.transmission.total_load_mw,
                "distribution_load_mw": combined.distribution.total_load_kw / 1000.0,
                "coupling_port": asdict(combined.coupling_port),
                "voltage_limits": combined.voltage_limits,
                "result": _as_serializable_result(combined.result) if combined.result else None,
            }
            rows = [payload]
        elif export_type == "voltages":
            rows = self._voltage_rows(combined)
        elif export_type == "violations":
            rows = self._voltage_violations(combined)
        elif export_type == "weak_locations":
            rows = self._rank_weak_locations(combined)
        else:
            return f"Error: Invalid export_type '{export_type}'."

        if file_format == "json":
            path.write_text(json.dumps(rows if export_type != "summary" else rows[0], indent=2, default=str), encoding="utf-8")
        elif file_format == "csv":
            if not rows:
                path.write_text("", encoding="utf-8")
            else:
                with path.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                    writer.writeheader()
                    writer.writerows(rows)
        else:
            return f"Error: Invalid file_format '{file_format}'."

        return f"Exported combined T&D {export_type} to '{path}' ({len(rows)} rows)."

    def _voltage_rows(self, combined: CombinedTDNetwork) -> list[dict]:
        rows = []
        for bus_id, bus in sorted(combined.transmission.buses.items()):
            rows.append(
                {
                    "system": "transmission",
                    "id": bus_id,
                    "name": bus.name,
                    "voltage_pu": bus.voltage_pu,
                    "nominal_voltage": bus.base_kv,
                    "raw_voltage": bus.voltage_pu,
                    "raw_voltage_units": "p.u.",
                }
            )
        for name, bus in sorted(combined.distribution.buses.items()):
            rows.append(
                {
                    "system": "distribution",
                    "id": name,
                    "name": name,
                    "voltage_pu": bus.voltage_pu,
                    "nominal_voltage": bus.nominal_voltage_v,
                    "raw_voltage": bus.voltage_v,
                    "raw_voltage_units": "V",
                }
            )
        return rows

    def _voltage_violations(self, combined: CombinedTDNetwork) -> list[dict]:
        limits = combined.voltage_limits
        violations = []
        for bus_id, bus in sorted(combined.transmission.buses.items()):
            vmin = limits["transmission_vmin_pu"]
            vmax = limits["transmission_vmax_pu"]
            severity = _violation_severity(bus.voltage_pu, vmin, vmax)
            if severity > 0:
                violations.append(
                    {
                        "system": "transmission",
                        "id": bus_id,
                        "voltage_pu": bus.voltage_pu,
                        "vmin_pu": vmin,
                        "vmax_pu": vmax,
                        "severity_pu": severity,
                    }
                )
        for name, bus in sorted(combined.distribution.buses.items()):
            vmin = limits["distribution_vmin_pu"]
            vmax = limits["distribution_vmax_pu"]
            severity = _violation_severity(bus.voltage_pu, vmin, vmax)
            if severity > 0:
                violations.append(
                    {
                        "system": "distribution",
                        "id": name,
                        "voltage_pu": bus.voltage_pu,
                        "vmin_pu": vmin,
                        "vmax_pu": vmax,
                        "severity_pu": severity,
                    }
                )
        return violations

    def _rank_weak_locations(self, combined: CombinedTDNetwork) -> list[dict]:
        limits = combined.voltage_limits
        weak = []
        for bus_id, bus in sorted(combined.transmission.buses.items()):
            vmin = limits["transmission_vmin_pu"]
            vmax = limits["transmission_vmax_pu"]
            severity = _violation_severity(bus.voltage_pu, vmin, vmax)
            weak.append(
                {
                    "system": "transmission",
                    "id": bus_id,
                    "voltage_pu": bus.voltage_pu,
                    "severity_pu": severity,
                }
            )
        for name, bus in sorted(combined.distribution.buses.items()):
            vmin = limits["distribution_vmin_pu"]
            vmax = limits["distribution_vmax_pu"]
            severity = _violation_severity(bus.voltage_pu, vmin, vmax)
            weak.append(
                {
                    "system": "distribution",
                    "id": name,
                    "voltage_pu": bus.voltage_pu,
                    "severity_pu": severity,
                }
            )
        return sorted(weak, key=lambda item: (item["severity_pu"], 1.0 - item["voltage_pu"]), reverse=True)

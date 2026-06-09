from __future__ import annotations

import json
import warnings
from itertools import count
from pathlib import Path
from typing import Any, Callable, List, Literal, Optional, Type

import numpy as np
import pandas as pd
from pydantic import BaseModel

try:
    import geopandas as gpd
except Exception:  # pragma: no cover - optional dependency guard
    gpd = None

try:
    import fiona
except Exception:  # pragma: no cover - optional dependency guard
    fiona = None

from distgrid_bench.tools.decorators import agent_tool
from distgrid_bench.tools import tool_config as config
from distgrid_bench.tools.shared_registry import SharedRegistry


def load_geojson(geojson_path):
    if gpd is None:
        raise ImportError("geopandas is required to load GeoJSON files.")
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r".*Non-conformant content for record .* successfully parsed.*",
        )
        return gpd.read_file(geojson_path)


def _read_vector_file(path, **kwargs):
    if gpd is None:
        raise ImportError("geopandas is required to load GeoJSON/GeoPackage files.")
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r".*Non-conformant content for record .* successfully parsed.*",
        )
        return gpd.read_file(path, **kwargs)


def save_geojson(gdf, output_path):
    gdf.to_file(output_path, driver="GeoJSON")


def filter_generator_substation_feeder(gdf, substation, feeder):
    gdf = gdf.copy()
    gdf["gs_generator_system_size_clean"] = pd.to_numeric(
        gdf["gs_generator_system_size"], errors="coerce"
    )
    mask = pd.Series([True] * len(gdf), index=gdf.index)
    if substation is not None:
        mask &= gdf["gs_substation"].astype(str).str.strip() == str(substation)
    if feeder is not None:
        mask &= gdf["gs_feeder_number"].astype(str).str.strip() == str(feeder)
    return gdf[mask]


def valid_generators(gdf):
    return gdf[gdf["gs_generator_system_size_clean"] > 0]


class Pv_system:
    """Represents a photovoltaic array."""

    _ids = count(0)

    def __init__(
        self,
        meter_number: int,
        capacity: Optional[float],
        Isc: Optional[float],
        Voc: Optional[float],
        Imp: Optional[float],
        Vmp: Optional[float],
        Ns: Optional[int],
        azimuth: Optional[float],
        tilt_angle: Optional[float],
        ideality_factor: Optional[float],
        latitude: Optional[float],
        longitude: Optional[float],
        panel_number: Optional[int],
        install_date: Optional[str] = None,
        inverter_model: Optional[str] = None,
        system_type: Optional[str] = None,
    ) -> None:
        self.id = next(self._ids)
        self.meter_number = meter_number
        self.capacity = capacity
        self.Isc = Isc
        self.Voc = Voc
        self.Imp = Imp
        self.Vmp = Vmp
        self.Ns = Ns
        self.azimuth = azimuth
        self.tilt_angle = tilt_angle
        self.n = ideality_factor
        self.latitude = latitude
        self.longitude = longitude
        self.panel_number = panel_number
        self.install_date = install_date
        self.inverter_model = inverter_model
        self.system_type = system_type
        # Derived for filtering convenience
        self.install_year = self._parse_year(install_date)
        self.I_ph = None
        self.I_0 = None
        self.Rs = None
        self.Rsh = None
        self.irr_STC = 1000.0
        self.T_STC = 25.0 + 273.15
        self.k = 1.38064852e-23
        self.q = 1.602176634e-19


    @staticmethod
    def _parse_year(date_str):
        if not date_str:
            return None
        try:
            return int(str(date_str).split("-")[0].split("/")[-1][:4])
        except (ValueError, IndexError):
            return None


Pv_system.bus2index_dict = {}
Pv_system.bus_id_counter = count(0)


class PVModel:
    def __init__(self):
        self.pv_systems: List[Pv_system] = []

    def create_pv_system(
        self,
        meter_number: int,
        Isc: float = None,
        Voc: float = None,
        Imp: float = None,
        Vmp: float = None,
        Ns: int = None,
        capacity: float = None,
        azimuth: float = None,
        tilt_angle: float = None,
        ideality_factor: float = None,
        latitude: float = None,
        longitude: float = None,
        panel_number: int = 0,
        install_date: str = None,
        inverter_model: str = None,
        system_type: str = None,
    ) -> Pv_system:
        pv_system = Pv_system(
            meter_number=meter_number,
            Isc=Isc,
            Voc=Voc,
            Imp=Imp,
            Vmp=Vmp,
            Ns=Ns,
            capacity=capacity,
            azimuth=azimuth,
            tilt_angle=tilt_angle,
            ideality_factor=ideality_factor,
            latitude=latitude,
            longitude=longitude,
            panel_number=panel_number,
            install_date=install_date,
            inverter_model=inverter_model,
            system_type=system_type,
        )
        self.pv_systems.append(pv_system)
        return pv_system


class PVLoader:
    def __init__(self, registry: SharedRegistry):
        self.registry = registry
        self.existing_pv_file = None

    @staticmethod
    def _synthetic_dataset(dataset_name: str) -> pd.DataFrame:
        """Small deterministic PV fixture used when optional geospatial readers are absent."""
        rows = []
        base_names = {
            "vec": ("Residential", "Enphase IQ7"),
            "gmp": ("Commercial", "SolarEdge SE7600"),
            "bed": ("Municipal", "SMA Sunny Boy"),
        }
        system_type, inverter = base_names.get(dataset_name, base_names["vec"])
        for idx in range(1, 31):
            rows.append(
                {
                    "gs_meter_number": f"{dataset_name.upper()}-{idx:04d}",
                    "gs_generator_system_size": 5.0 + idx * 0.75,
                    "gs_substation": "29" if dataset_name == "vec" else "14",
                    "gs_feeder_number": "3" if dataset_name == "vec" else "1",
                    "gs_net_mtr_in_svc_date": f"{2015 + (idx % 9)}-07-01",
                    "gs_inverter_manufacturer": inverter if idx % 3 else f"{inverter} Plus",
                    "gs_system_type": system_type if idx % 4 else "Residential",
                    "geometry": None,
                }
            )
        if dataset_name == "gmp":
            rows.append(
                {
                    "gs_meter_number": "GMP-OUTLIER",
                    "gs_generator_system_size": 750.0,
                    "gs_substation": "14",
                    "gs_feeder_number": "1",
                    "gs_net_mtr_in_svc_date": "2021-09-15",
                    "gs_inverter_manufacturer": "SolarEdge Utility",
                    "gs_system_type": "Commercial",
                    "geometry": None,
                }
            )
        return pd.DataFrame(rows)

    def load_user_pv_model(self, model_name: str = "user_default") -> str:
        """
        Load a user-defined PV system layout from a JSON model file.

        Args:
            model_name: Key in the PV_MODELS config registry (default 'user_default').

        Returns:
            str: Count of PV systems loaded and source file name.
        """
        ipv_file = config.PV_MODELS.get(model_name)
        if ipv_file is None:
            return f"Error: Model name '{model_name}' not found in PV_MODELS configuration."

        ipv_file = Path(ipv_file)
        try:
            user_pv_model = self.import_pv_data(ipv_file)
            self.registry.set("pv:active", user_pv_model)
            return (
                f"User-defined PV model '{model_name}' loaded successfully. "
                f"{len(user_pv_model.pv_systems)} PV active. Source: {ipv_file.name}"
            )
        except Exception as e:
            return f"Error loading user PV model '{model_name}': {str(e)}"

    def import_pv_data(self, pv_file) -> PVModel:
        pv_file = Path(pv_file)
        if not pv_file.exists():
            raise FileNotFoundError(f"PV file not found: {pv_file}")

        with open(pv_file) as f:
            pv_data = json.load(f)

        pv_model = PVModel()
        for _, specs in pv_data.items():
            location = specs.get("location", {})
            inverter = specs.get("inverter", {})
            modules = specs.get("modules", {})
            installation = specs.get("installation", {})
            elec_specs = modules.get("electrical_specifications", {}).get("front_side", {})

            pv_model.create_pv_system(
                meter_number=specs.get("meter_number", location.get("meter_number")),
                Isc=specs.get("Isc", elec_specs.get("isc", 0.0)),
                Voc=specs.get("Voc", elec_specs.get("voc", 0.0)),
                Imp=specs.get("Imp", elec_specs.get("imp", 0.0)),
                Vmp=specs.get("Vmp", elec_specs.get("vmp", 0.0)),
                Ns=specs.get("Ns", 0),
                capacity=specs.get("capacity", inverter.get("capacity", 0.0)),
                azimuth=specs.get("azimuth", installation.get("azimuth", 180.0)),
                tilt_angle=specs.get("tilt_angle", installation.get("tilt", 0.0)),
                ideality_factor=specs.get("ideality_factor", 1.2),
                latitude=specs.get("latitude", location.get("latitude", 0.0)),
                longitude=specs.get("longitude", location.get("longitude", 0.0)),
                panel_number=specs.get("panel_number", installation.get("panel_number", 0)),
            )
        return pv_model

    @agent_tool
    def load_pv_dataset(
        self,
        dataset_name: Literal["vec", "gmp", "bed"] = "vec",
        substation_id: Optional[Any] = None,
        feeder_id: Optional[Any] = None,
    ) -> str:
        """
        Load a PV interconnection dataset filtered by substation and feeder.

        Args:
            dataset_name: Dataset key: vec (Vermont Electric Cooperative), gmp (Green Mountain Power), or bed (Burlington Electric).
            substation_id: Substation identifier for filtering rows.
            feeder_id: Feeder number for filtering rows.

        Returns:
            str: Count of active PV systems loaded from the filtered dataset.
        """
        self.selected_path = config.PV_DATASETS.get(dataset_name, config.PV_DATASETS["vec"])
        path_obj = Path(self.selected_path)
        used_synthetic = False

        try:
            if not path_obj.exists() or gpd is None:
                self.raw_gdf = self._synthetic_dataset(dataset_name)
                used_synthetic = True
            elif path_obj.suffix == ".gpkg":
                try:
                    self.raw_gdf = _read_vector_file(path_obj, layer="Generators")
                except ValueError:
                    try:
                        self.raw_gdf = _read_vector_file(path_obj, layer="meters")
                    except ValueError:
                        self.raw_gdf = _read_vector_file(path_obj)
            else:
                self.raw_gdf = load_geojson(path_obj)
        except Exception as e:
            return f"Error loading file: {str(e)}"

        filtered = filter_generator_substation_feeder(
            self.raw_gdf, substation_id, feeder_id
        )
        if filtered.empty:
            return "Warning: Filter resulted in empty dataset. No data loaded."

        self.valid_gdf = valid_generators(filtered)
        self.existing_pv_file = [None, None, self.valid_gdf]
        result = self.load_existing_pv_data()
        filterable = "install_year, install_date, inverter_model, system_type, capacity"
        source_note = "synthetic fallback" if used_synthetic else path_obj.name
        return (
            f"Loaded '{dataset_name}' from {source_note}: {len(self.valid_gdf)} systems active. "
            f"({result}) Filterable attributes: {filterable}."
        )

    def load_existing_pv_data(self) -> str:
        if not hasattr(self, "existing_pv_file") and not hasattr(self, "valid_gdf"):
            return "Error: No existing PV data imported."

        if not hasattr(self, "existing_pv_file") or self.existing_pv_file is None:
            self.existing_pv_file = [None, None, self.valid_gdf]

        try:
            pv_model = PVModel()
            if not isinstance(self.existing_pv_file, list) or len(self.existing_pv_file) < 3:
                return "Error: Internal data buffer is invalid."

            df_existing = self.existing_pv_file[2]
            count_loaded = 0
            for _, row in df_existing.iterrows():
                meter_number = row.get("gs_meter_number", None)
                raw_capacity = row.get("gs_generator_system_size_clean", 0)
                capacity = raw_capacity / 0.8 if raw_capacity else 0
                geometry = row.get("geometry", None)
                if geometry is not None and hasattr(geometry, "y") and hasattr(geometry, "x"):
                    latitude = geometry.y
                    longitude = geometry.x
                else:
                    latitude, longitude = 0, 0

                pv_model.create_pv_system(
                    meter_number=meter_number,
                    capacity=capacity,
                    tilt_angle=10.0,
                    azimuth=180.0,
                    latitude=latitude,
                    longitude=longitude,
                    install_date=str(row.get("gs_net_mtr_in_svc_date", "")),
                    inverter_model=str(row.get("gs_inverter_manufacturer", "Unknown")),
                    system_type=str(row.get("gs_system_type", "Unknown")),
                )
                count_loaded += 1

            self.registry.set("pv:active", pv_model)
            return f"Existing PV model loaded. {count_loaded} PV systems registered as 'pv:active'."
        except Exception as e:
            return f"Error loading existing PV data: {str(e)}"

    def check_geojson(self, dataset_name: str = "vec"):
        """
        Validate that a GeoPackage or GeoJSON dataset file is readable and inspect its structure.

        Args:
            dataset_name: Dataset key in PV_DATASETS config (vec, gmp, or bed).

        Returns:
            bool: True if the file loaded successfully, False otherwise. Prints row and column info.
        """
        path_val = config.PV_DATASETS.get(dataset_name)
        if not path_val:
            return f"Error: Dataset '{dataset_name}' not found in config."

        file_path = Path(path_val)
        print(f"Checking file: {file_path}")
        try:
            if gpd is None:
                return "Error: geopandas is required to validate GeoJSON/GeoPackage files."
            if fiona is not None and file_path.suffix == ".gpkg":
                layers = fiona.listlayers(file_path)
                if "meters" in layers:
                    print("Reading layer 'meters' from GeoPackage...")
                    gdf = _read_vector_file(file_path, layer="meters")
                else:
                    print(f"Layer 'meters' not found. Available: {layers}")
                    gdf = _read_vector_file(file_path, layer=layers[0])
            else:
                gdf = _read_vector_file(file_path)

            print(f"Successfully loaded. Rows: {len(gdf)}")
            print(f"Columns: {list(gdf.columns)}")
            return True
        except Exception as e:
            print(f"Error checking GeoJSON: {e}")
            return False


class PVAnalyzer:
    def __init__(self, registry: SharedRegistry):
        self.registry = registry

    @property
    def pv_systems(self):
        pv_model = self.registry.get("pv:active")
        if pv_model and hasattr(pv_model, "pv_systems"):
            return pv_model.pv_systems
        return []

    @agent_tool
    def count_pv_systems(self, scope: Literal["active_model", "all"] = "active_model") -> str:
        """
        Return the count of PV systems in the active model.

        Args:
            scope: active_model reports the current filtered set; all reports the full dataset.

        Returns:
            str: Total number of active PV systems.
        """
        if not self.pv_systems:
            return "Error: No PV systems loaded."
        return f"Total number of PV systems ({scope}): {len(self.pv_systems)}"

    @agent_tool
    def get_substation(self, source: Literal["metadata", "inference"] = "metadata") -> str:
        """
        Return the substation identifier associated with the loaded PV dataset.

        Args:
            source: metadata reads from file metadata; inference uses heuristics.

        Returns:
            str: Substation identifier.
        """
        return f"Substation ({source}): 29"

    @agent_tool
    def get_feeder(self, source: Literal["metadata", "inference"] = "metadata") -> str:
        """
        Return the feeder number associated with the loaded PV dataset.

        Args:
            source: metadata reads from file metadata; inference uses heuristics.

        Returns:
            str: Feeder number.
        """
        return f"Feeder ({source}): 3"

    @agent_tool
    def load_pv_weather_data(
        self,
        start_date: str = "2016-07-01",
        end_date: str = "2016-07-01",
        check_time: bool = False,
        source: Literal["local", "remote"] = "local",
    ) -> str:
        """
        Attach weather data to all active PV systems for a given date range.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            check_time: If True, validate time alignment between weather and PV data.
            source: local uses cached weather files; remote fetches from an external source.

        Returns:
            str: Count of PV systems updated and the date range loaded.
        """
        if not self.pv_systems:
            return "Error: No PV systems to attach weather data to."
        for pv in self.pv_systems:
            pv.weather_data = "Loaded"
        return f"Weather data loaded successfully for {len(self.pv_systems)} PV systems (Period: {start_date} to {end_date})."

    @agent_tool
    def compute_poa_irradiance(
        self,
        start_date: str = "2016-07-01",
        end_date: str = "2016-07-01",
        start_time: str = "00:00:00",
        end_time: str = "23:59:59",
    ) -> str:
        """
        Compute plane-of-array irradiance for all active PV systems.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            start_time: Start time of day in HH:MM:SS format.
            end_time: End time of day in HH:MM:SS format.

        Returns:
            str: Count of PV systems with computed POA and the analysis period.
        """
        if not self.pv_systems:
            return "Error: No PV systems available."

        period = {
            "Start Date": start_date,
            "End Date": end_date,
            "Start Time": start_time,
            "End Time": end_time,
        }

        count_loaded = 0
        try:
            for pv in self.pv_systems:
                if not hasattr(pv, "weather_data") or pv.weather_data is None:
                    continue
                pv.POA_data = "Computed"
                count_loaded += 1

            if count_loaded == 0:
                return "Warning: Weather data not loaded for any PV system."
            return f"POA Irradiance computed for {count_loaded} systems for period {period}."
        except Exception as e:
            return f"Error computing POA: {str(e)}"

    @agent_tool
    def estimate_pv_parameters(self, solver: str = "ipopt", verbose: bool = False) -> str:
        """
        Estimate diode-model electrical parameters (I_ph, I_0, Rs, Rsh) for all active PV systems.

        Args:
            solver: Nonlinear solver to use for parameter estimation (e.g., ipopt).
            verbose: If True, include per-system solver convergence details.

        Returns:
            str: Count of PV systems with estimated parameters and solver used.
        """
        if not self.pv_systems:
            return "Error: No PV systems available for estimation."
        for pv in self.pv_systems:
            pv.estimated_params = True
        verbose_msg = f" (Verbose mode: {verbose})" if verbose else ""
        return f"Estimated electrical parameters for {len(self.pv_systems)} PV systems using '{solver}'.{verbose_msg}"

    @agent_tool
    def filter_pv_systems(
        self,
        key: str,
        value: str,
        operator: Literal["contains", "equals", "starts_with", "gt", "lt"] = "contains",
    ) -> str:
        """
        Filter the active PV systems by an attribute value.

        Args:
            key: PV system attribute to filter on (e.g., 'system_type', 'inverter_model', 'capacity').
            value: Value to compare against.
            operator: Comparison operator: contains, equals, starts_with, gt (greater than), or lt (less than).

        Returns:
            str: Count of systems kept and total systems before filtering.
        """
        if not self.pv_systems:
            return "Error: No PV systems loaded to filter."

        original_count = len(self.pv_systems)
        filtered_systems = []
        for pv in self.pv_systems:
            attr_val = str(getattr(pv, key, ""))
            if operator == "contains" and value in attr_val:
                filtered_systems.append(pv)
            elif operator == "equals" and value == attr_val:
                filtered_systems.append(pv)
            elif operator == "starts_with" and attr_val.startswith(value):
                filtered_systems.append(pv)
            elif operator in {"gt", "lt"}:
                try:
                    attr_num = float(attr_val)
                    value_num = float(value)
                except (TypeError, ValueError):
                    continue
                if operator == "gt" and attr_num > value_num:
                    filtered_systems.append(pv)
                elif operator == "lt" and attr_num < value_num:
                    filtered_systems.append(pv)

        if not filtered_systems:
            return (
                f"Warning: Filter `{key} {operator} '{value}'` matched 0 of "
                f"{original_count} systems. Active PV systems were left unchanged."
            )

        pv_model = self.registry.get("pv:active")
        pv_model.pv_systems = filtered_systems
        self.registry.set("pv:active", pv_model)
        return f"Filtered PV systems by `{key} {operator} '{value}'`. Kept {len(filtered_systems)} of {original_count} systems."

    def check_metadata_integrity(
        self,
        strict: bool = False,
        required_fields: Optional[str] = None,
    ) -> str:
        """
        Check PV system metadata completeness for installation dates, inverter models, and capacities.

        Args:
            strict: If True, apply stricter completeness requirements.
            required_fields: Optional comma-separated field names to check explicitly.

        Returns:
            str: Counts of missing fields and overall data quality assessment.
        """
        if not self.pv_systems:
            return "Error: No PV systems loaded."

        missing_install = [
            pv.id for pv in self.pv_systems
            if not pv.install_date or pv.install_date in ["NaT", "None", "", "nan"]
        ]
        missing_inverter = [
            pv.id for pv in self.pv_systems
            if not pv.inverter_model or pv.inverter_model == "Unknown"
        ]
        missing_cap = [pv.id for pv in self.pv_systems if not pv.capacity]

        report = "Metadata Integrity Report:\n"
        report += f"  - Missing Installation Date: {len(missing_install)} systems\n"
        report += f"  - Missing Inverter Model: {len(missing_inverter)} systems\n"
        report += f"  - Missing Capacity: {len(missing_cap)} systems\n"
        if required_fields:
            report += f"\n  - Requested fields checked: {required_fields}"
        if strict:
            report += "\n  - Strict mode: enabled"
        report += "\n  * Data Quality: Excellent." if len(missing_install) == 0 and len(missing_inverter) == 0 else "\n  ! Data Quality: Warning - Some fields incomplete."
        return report

    @agent_tool
    def compare_with_feeder(self, dataset_name: str, substation_id: str, feeder_id: str) -> str:
        """
        Compare the active PV dataset capacity against another feeder's data.

        Args:
            dataset_name: Dataset key for the comparison feeder (vec, gmp, or bed).
            substation_id: Substation identifier for the target feeder.
            feeder_id: Feeder number for the target feeder.

        Returns:
            str: System count, total capacity, and delta between active and target feeder.
        """
        active_count = len(self.pv_systems)
        active_cap = sum([pv.capacity or 0 for pv in self.pv_systems])
        return (
            f"Comparative Analysis vs {substation_id}/{feeder_id}:\n"
            f"  - Active Feeder: {active_count} systems, {active_cap:.2f} kW\n"
            f"  - Target Feeder ({substation_id}/{feeder_id}): 250 systems, 850.00 kW (Mock)\n"
            f"  - Delta: Active is {active_cap - 850:.2f} kW larger."
        )

    def analyze_capacity_distribution(self, bins: int = 10) -> str:
        if not self.pv_systems:
            return "Error: No PV systems loaded."

        capacities = [pv.capacity for pv in self.pv_systems if pv.capacity is not None]
        if not capacities:
            return "Warning: No capacity data available."

        hist, bin_edges = np.histogram(capacities, bins=bins)
        result = "Capacity Distribution (kW):\n"
        for i in range(len(hist)):
            if hist[i] > 0:
                result += f"  [{bin_edges[i]:.1f} - {bin_edges[i+1]:.1f}]: {hist[i]} systems\n"
        return result

    def analyze_temporal_growth(self, freq: str = "Y") -> str:
        if not self.pv_systems:
            return "Error: No PV systems loaded."

        data = []
        for pv in self.pv_systems:
            if hasattr(pv, "install_date") and pv.install_date:
                if str(pv.install_date) not in ["NaT", "None", "", "nan"]:
                    data.append(
                        {
                            "date": pd.to_datetime(pv.install_date, errors="coerce"),
                            "capacity": pv.capacity or 0,
                        }
                    )

        data = [d for d in data if not pd.isna(d["date"])]
        if not data:
            return "Warning: No valid installation date metadata available."

        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        growth = df.resample(freq).sum().cumsum()

        result = f"Cumulative PV Capacity Growth ({freq}):\n"
        for date, row in growth.tail(5).iterrows():
            result += f"  {date.strftime('%Y-%m-%d')}: {row['capacity']:.2f} kW\n"
        return result

    @agent_tool
    def detect_missing_values(
        self,
        columns: Optional[list[str]] = None,
        **kwargs,
    ) -> str:
        """
        Detect missing or null values in PV system metadata fields.

        Args:
            columns: Preferred list of column names to check.

        Returns:
            str: Metadata integrity report with missing value counts per field.
        """
        field = kwargs.get("field")
        required_fields = kwargs.get("required_fields")
        if columns:
            fields = ", ".join(columns)
        else:
            fields = required_fields or field
        return self.check_metadata_integrity(required_fields=fields)

    @agent_tool
    def analyze_distribution(self, metric: str = "capacity", bins: int = 10) -> str:
        """
        Analyze the statistical distribution of a PV system metric.

        Args:
            metric: Metric to analyze (currently only 'capacity' is supported).
            bins: Number of histogram bins.

        Returns:
            str: Histogram of system counts per capacity range in kW.
        """
        if metric != "capacity":
            return f"Error: Unsupported metric '{metric}'."
        return self.analyze_capacity_distribution(bins=bins)

    @agent_tool
    def analyze_growth(self, freq: Literal["Y", "M"] = "Y") -> str:
        """
        Analyze cumulative PV capacity growth over time using installation date metadata.

        Args:
            freq: Aggregation frequency: YE for yearly or ME for monthly.

        Returns:
            str: Cumulative capacity growth over the most recent periods.
        """
        freq = {"Y": "YE", "M": "ME"}.get(freq, freq)
        return self.analyze_temporal_growth(freq=freq)

    @agent_tool
    def analyze_market_share(self) -> str:
        """
        Compute inverter manufacturer market share among active PV systems.

        Returns:
            str: Percentage share per inverter manufacturer.
        """
        if not self.pv_systems:
            return "Error: No PV systems loaded."

        models = [str(pv.inverter_model or "Unknown") for pv in self.pv_systems]
        counts = pd.Series(models).value_counts(dropna=False)
        total = len(models)
        lines = ["Inverter Market Share:"]
        for name, count_val in counts.items():
            lines.append(f"  - {name}: {count_val / total * 100:.1f}%")
        return "\n".join(lines)

    @agent_tool
    def detect_outliers(self, metric: str = "capacity", percentile: float = 99.0) -> str:
        """
        Identify PV systems with outlier capacity values above a percentile threshold.

        Args:
            metric: Metric to check for outliers (currently only 'capacity' is supported).
            percentile: Percentile threshold above which systems are flagged as outliers.

        Returns:
            str: Count of outlier systems detected at the given percentile.
        """
        if not self.pv_systems:
            return "Error: No PV systems loaded."
        if metric != "capacity":
            return f"Error: Unsupported metric '{metric}'."
        values = [pv.capacity for pv in self.pv_systems if pv.capacity is not None]
        if not values:
            return "Warning: No capacity data available."
        threshold = np.percentile(values, percentile)
        outliers = [pv for pv in self.pv_systems if (pv.capacity or 0) >= threshold]
        return f"Detected {len(outliers)} outliers at the {percentile}th percentile."

    @agent_tool
    def audit_metadata_integrity(
        self,
        strict: bool = False,
        required_fields: Optional[str] = None,
    ) -> str:
        """
        Audit PV system metadata completeness and flag missing or default values.

        Args:
            strict: If True, apply stricter completeness requirements.
            required_fields: Optional comma-separated field names to include in the audit.

        Returns:
            str: Audit report with missing field counts and overall data quality rating.
        """
        return self.check_metadata_integrity(strict=strict, required_fields=required_fields)

    @agent_tool
    def validate_value_ranges(
        self,
        min_capacity_kw: float = 0.0,
        max_capacity_kw: float = 5000.0,
        checks: Optional[dict[str, list[float]]] = None,
    ) -> str:
        """
        Validate that PV system capacity values fall within acceptable physical bounds.

        Args:
            min_capacity_kw: Minimum acceptable capacity in kW.
            max_capacity_kw: Maximum acceptable capacity in kW.
            checks: Optional dict mapping field names to [min, max] bounds.

        Returns:
            str: Validation result with count of out-of-range systems detected.
        """
        if not self.pv_systems:
            return "Error: No PV systems loaded."
        if checks and "capacity" in checks:
            min_capacity_kw, max_capacity_kw = checks["capacity"]
        invalid = [
            pv.id for pv in self.pv_systems
            if (pv.capacity or 0) < min_capacity_kw or (pv.capacity or 0) > max_capacity_kw
        ]
        return f"Logic validation passed for 1 rules. No range violations found." if not invalid else f"Found {len(invalid)} systems with invalid values."

    def summarize_pv_readiness(self, verbosity: Literal["high", "low"] = "high") -> str:
        """
        Return a generation readiness summary for the active PV model.

        Args:
            verbosity: high includes detailed output; low returns a compact summary.

        Returns:
            str: Summary of PV generation status.
        """
        return f"Generation summary ready. (Verbosity: {verbosity})"


class PVGeneration(PVAnalyzer):
    def __init__(self, registry: SharedRegistry):
        super().__init__(registry)

    def _calculate_pv_flow(self, method: Literal["auto", "capacity", "diode"] = "auto", timestamp: str = None) -> str:
        """
        Calculate DC power output for all active PV systems.

        Args:
            method: auto selects the best available model, capacity uses simple scaling, diode uses the full single-diode model.
            timestamp: Optional timestamp for irradiance-based calculation.

        Returns:
            str: Total DC power output in kW and count of systems per calculation method.
        """
        if not self.pv_systems:
            return "Error: No active PV systems found."

        results = {}
        count_cap = 0
        count_full = 0
        try:
            for pv in self.pv_systems:
                use_full = method == "diode" or (method == "auto" and getattr(pv, "I_ph", None) is not None)
                if use_full:
                    pv.MPPT_DC_power_output = (pv.capacity * 1000) * 0.95
                    count_full += 1
                else:
                    pv.MPPT_DC_power_output = (pv.capacity * 1000) * 0.8 if pv.capacity else 0.0
                    count_cap += 1 if pv.capacity else 0
                results[pv.id] = pv.MPPT_DC_power_output

            total_p = sum(results.values())
            return (
                f"PV Generation Calculation Complete (Method: {method}).\n"
                f" - {count_full} systems used Full Diode Model.\n"
                f" - {count_cap} systems used Capacity Estimation.\n"
                f" - Total DC Power Output: {total_p/1000:.2f} kW"
            )
        except Exception as e:
            return f"Error calculating PV generation: {str(e)}"

    @agent_tool
    def apply_capacity_scaling(self, factor: float) -> str:
        """
        Scale all active PV system capacities by a constant factor.

        Args:
            factor: Multiplier applied to each system's capacity.

        Returns:
            str: Count of systems scaled and the factor applied.
        """
        if not self.pv_systems:
            return "Error: No PV systems loaded."
        count_scaled = 0
        for pv in self.pv_systems:
            if pv.capacity:
                pv.capacity *= factor
                count_scaled += 1
        return f"Successfully scaled capacity by factor {factor} for {count_scaled} systems."

    def cap_to_power(self, pv):
        return (pv.capacity * 1000) * 0.8

    @agent_tool
    def set_calculation_method(self, method: Literal["auto", "capacity", "diode"] = "auto", timestamp: str = None) -> str:
        """
        Configure the PV calculation method.

        Args:
            method: auto, capacity (simple scaling), or diode (single-diode model).
            timestamp: Optional timestamp to fix the irradiance calculation window.

        Returns:
            str: Confirmation of the configured method and optional timestamp.
        """
        self.gen_config = {"method": method, "timestamp": timestamp}
        return f"Calculation method set to '{method}'" + (f" at {timestamp}" if timestamp else "")

    @agent_tool
    def initialize_pv_output_model(self) -> str:
        """
        Assemble the generation model from calibrated parameters and irradiance inputs.

        Loads the estimated electrical parameters (I_ph, I_0, Rs, Rsh for the diode
        model, or rated capacity for the capacity method) together with the computed
        plane-of-array irradiance into the internal calculation engine for each PV
        system. The output calculation reads directly from this assembled model state.

        Returns:
            str: Number of systems initialized and the active calculation method.
        """
        systems = self.pv_systems
        if not systems:
            return "Error: No PV systems available."
        method = getattr(self, "gen_config", {}).get("method", "auto") if hasattr(self, "gen_config") else "auto"
        initialized = 0
        for pv in systems:
            if getattr(pv, "estimated_params", False) or getattr(pv, "POA_data", None):
                pv.model_initialized = True
                initialized += 1
        return (
            f"PV output model initialized for {initialized} of {len(systems)} systems "
            f"using '{method}' method."
        )

    @agent_tool
    def calculate_pv_output(self, execution_mode: Literal["sequential", "parallel"] = "sequential") -> str:
        """
        Run the PV generation output calculation.

        Args:
            execution_mode: sequential or parallel execution across PV systems.

        Returns:
            str: Confirmation that the calculation was executed and the mode used.
        """
        if not hasattr(self, "gen_config"):
            self.gen_config = {"method": "auto", "timestamp": None}
        self.last_gen_result = self._calculate_pv_flow(
            method=self.gen_config["method"], timestamp=self.gen_config["timestamp"]
        )
        return f"PV output calculation executed (Mode: {execution_mode})."

    @agent_tool
    def summarize_pv_generation(self, verbosity: Literal["high", "low"] = "high") -> str:
        """
        Return the result of the most recent PV generation calculation.

        Args:
            verbosity: high includes detailed output; low returns a compact summary.

        Returns:
            str: Generation result from the last calculate_pv_output call.
        """
        if not hasattr(self, "last_gen_result"):
            return "Error: No calculation executed."
        return f"{self.last_gen_result} (Verbosity: {verbosity})"

    def perturb_capacity(self, factor: float) -> str:
        """
        Apply a capacity perturbation factor to all active PV systems (alias for apply_capacity_scaling).

        Args:
            factor: Multiplier applied to each system's capacity.

        Returns:
            str: Count of systems scaled and the factor applied.
        """
        return self.apply_capacity_scaling(factor)


__all__ = [
    "Pv_system",
    "PVModel",
    "PVLoader",
    "PVAnalyzer",
    "PVGeneration",
    "load_geojson",
    "save_geojson",
    "filter_generator_substation_feeder",
    "valid_generators",
]

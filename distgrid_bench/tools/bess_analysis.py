"""
Single-file BESS backend for loading, analysis, simulation, and optimization.
"""

from __future__ import annotations

import json
import os
from typing import Literal, Optional

import numpy as np
import pandas as pd

from distgrid_bench.tools.decorators import agent_tool
from distgrid_bench.tools import tool_config as config
from distgrid_bench.tools.shared_registry import SharedRegistry


class BESSLoader:
    def __init__(self, registry: SharedRegistry):
        self.registry = registry

    @agent_tool
    def load_battery_specs(
        self,
        spec_name: Literal["lfp_100kwh", "nmc_100kwh"] = "lfp_100kwh",
        capacity_override_kwh: Optional[float] = None,
        power_override_kw: Optional[float] = None,
        efficiency_override: Optional[float] = None,
    ) -> str:
        """
        Load battery chemistry specifications into the shared registry.

        Args:
            spec_name: Battery spec file to load (lfp_100kwh or nmc_100kwh).
            capacity_override_kwh: Optional capacity override in kWh.
            power_override_kw: Optional power rating override in kW.
            efficiency_override: Optional round-trip efficiency override (0-1).

        Returns:
            str: Loaded battery name, capacity, power rating, and efficiency.
        """
        try:
            bess_dir = config.INPUT_DIR / "bess" / "battery_specs"
            spec_path = bess_dir / f"{spec_name}.json"

            if not spec_path.exists():
                available = sorted(f.stem for f in bess_dir.glob("*.json"))
                return f"Error: Spec '{spec_name}' not found. {len(available)} available: {', '.join(available)}."

            with open(spec_path) as f:
                specs = json.load(f)

            if capacity_override_kwh is not None:
                specs["capacity_kwh"] = capacity_override_kwh
            if power_override_kw is not None:
                specs["power_kw"] = power_override_kw
            if efficiency_override is not None:
                specs["roundtrip_efficiency"] = efficiency_override

            self.registry.set("bess:specs", specs)

            return (
                f"Loaded battery: {specs.get('name', spec_name)} | "
                f"Capacity: {specs.get('capacity_kwh')} kWh | "
                f"Power: {specs.get('power_kw')} kW | "
                f"Efficiency: {specs.get('roundtrip_efficiency', 0.9)*100:.0f}%"
            )
        except Exception as e:
            return f"Error loading battery specs: {str(e)}"

    @agent_tool
    def load_load_profile(
        self,
        profile_name: Literal["commercial_office", "residential_home"] = "commercial_office",
        scale_factor: float = 1.0,
        time_shift_hours: int = 0,
        hours_to_load: Optional[int] = None,
    ) -> str:
        """
        Load an hourly electrical load profile into the shared registry.

        Args:
            profile_name: Load profile to use (commercial_office or residential_home).
            scale_factor: Multiplier applied to all load values.
            time_shift_hours: Shift the profile timestamps by this many hours.
            hours_to_load: Limit the profile to this many hours.

        Returns:
            str: Peak load, average load, total energy, and duration loaded.
        """
        try:
            profile_dir = config.INPUT_DIR / "bess" / "load_profiles"
            profile_path = profile_dir / f"{profile_name}.csv"

            if not profile_path.exists():
                available = sorted(f.stem for f in profile_dir.glob("*.csv"))
                return f"Error: Profile '{profile_name}' not found. {len(available)} available: {', '.join(available)}."

            df = pd.read_csv(profile_path, parse_dates=["timestamp"])
            df = df.set_index("timestamp")

            if hours_to_load is not None:
                df = df.head(hours_to_load)

            df["load_kw"] = df["load_kw"] * scale_factor

            if time_shift_hours != 0:
                df.index = df.index + pd.Timedelta(hours=time_shift_hours)

            self.registry.set("bess:load_profile", df)

            peak_load = df["load_kw"].max()
            avg_load = df["load_kw"].mean()
            total_energy = df["load_kw"].sum()

            return (
                f"Loaded load profile: {profile_name} | "
                f"Peak: {peak_load:.1f} kW | Avg: {avg_load:.1f} kW | "
                f"Total: {total_energy:.1f} kWh ({len(df)} hours)"
                f"{f' | Scaled by {scale_factor}x' if scale_factor != 1.0 else ''}"
            )
        except Exception as e:
            return f"Error loading load profile: {str(e)}"

    @agent_tool
    def load_solar_profile(
        self,
        profile_name: Literal["50kw_array"] = "50kw_array",
        scale_factor: float = 1.0,
        cloud_cover_factor: float = 1.0,
        hours_to_load: Optional[int] = None,
    ) -> str:
        """
        Load an hourly solar generation profile into the shared registry.

        Args:
            profile_name: Solar profile to use (currently 50kw_array).
            scale_factor: Multiplier applied to all solar generation values.
            cloud_cover_factor: Additional attenuation factor for cloud cover (0-1).
            hours_to_load: Limit the profile to this many hours.

        Returns:
            str: Peak solar output, total generation, and duration loaded.
        """
        try:
            profile_dir = config.INPUT_DIR / "bess" / "solar_profiles"
            profile_path = profile_dir / f"{profile_name}.csv"

            if not profile_path.exists():
                available = sorted(f.stem for f in profile_dir.glob("*.csv"))
                return f"Error: Profile '{profile_name}' not found. {len(available)} available: {', '.join(available)}."

            df = pd.read_csv(profile_path, parse_dates=["timestamp"])
            df = df.set_index("timestamp")

            if hours_to_load is not None:
                df = df.head(hours_to_load)

            df["solar_kw"] = df["solar_kw"] * scale_factor * cloud_cover_factor

            self.registry.set("bess:solar_profile", df)

            peak_solar = df["solar_kw"].max()
            total_generation = df["solar_kw"].sum()

            return (
                f"Loaded solar profile: {profile_name} | "
                f"Peak: {peak_solar:.1f} kW | "
                f"Total: {total_generation:.1f} kWh ({len(df)} hours)"
                f"{f' | Scale: {scale_factor}x, Cloud: {cloud_cover_factor}' if scale_factor != 1.0 or cloud_cover_factor != 1.0 else ''}"
            )
        except Exception as e:
            return f"Error loading solar profile: {str(e)}"

    @agent_tool
    def load_tariff_structure(
        self,
        tariff_name: Literal["tou_summer", "flat_rate"] = "tou_summer",
        demand_charge_override: Optional[float] = None,
        energy_rate_multiplier: float = 1.0,
    ) -> str:
        """
        Load a utility tariff structure into the registry.

        Args:
            tariff_name: Tariff to load (tou_summer or flat_rate).
            demand_charge_override: Optional demand charge override in $/kW.
            energy_rate_multiplier: Multiplier applied to all energy rate values.

        Returns:
            str: Tariff name, rate period names, and demand charge rate.
        """
        try:
            tariff_dir = config.INPUT_DIR / "bess" / "tariffs"
            tariff_path = tariff_dir / f"{tariff_name}.json"

            if not tariff_path.exists():
                available = sorted(f.stem for f in tariff_dir.glob("*.json"))
                return f"Error: Tariff '{tariff_name}' not found. {len(available)} available: {', '.join(available)}."

            with open(tariff_path) as f:
                tariff = json.load(f)

            if demand_charge_override is not None:
                tariff["demand_charge_per_kw"] = demand_charge_override

            if energy_rate_multiplier != 1.0:
                for period in tariff.get("energy_rates", {}).values():
                    if "price_per_kwh" in period:
                        period["price_per_kwh"] *= energy_rate_multiplier

            self.registry.set("bess:tariff", tariff)

            rate_names = list(tariff.get("energy_rates", {}).keys())
            demand_charge = tariff.get("demand_charge_per_kw", 0)

            return (
                f"Loaded tariff: {tariff.get('name', tariff_name)} | "
                f"Rate Periods: {rate_names} | "
                f"Demand Charge: ${demand_charge:.2f}/kW"
            )
        except Exception as e:
            return f"Error loading tariff: {str(e)}"

    @agent_tool
    def load_grid_prices(
        self,
        source: Literal["sample", "volatile", "stable"] = "sample",
        price_multiplier: float = 1.0,
        hours: int = 24,
    ) -> str:
        """
        Load hourly wholesale grid prices into the registry.

        Args:
            source: Price profile shape: sample (typical day-night spread), volatile (high swings), or stable (flat).
            price_multiplier: Multiplier applied to all price values.
            hours: Number of hours to generate.

        Returns:
            str: Min, max, and spread of the generated price curve.
        """
        try:
            timestamps = pd.date_range("2024-07-15", periods=hours, freq="h")

            if source == "sample":
                base_prices = [
                    0.03, 0.025, 0.02, 0.02, 0.025, 0.03, 0.04, 0.06,
                    0.08, 0.10, 0.12, 0.14, 0.15, 0.18, 0.22, 0.25,
                    0.23, 0.18, 0.12, 0.08, 0.06, 0.05, 0.04, 0.035,
                ]
            elif source == "volatile":
                base_prices = [
                    0.02, 0.015, 0.01, 0.01, 0.015, 0.02, 0.05, 0.10,
                    0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50,
                    0.40, 0.30, 0.20, 0.10, 0.08, 0.05, 0.03, 0.02,
                ]
            else:
                base_prices = [
                    0.10, 0.095, 0.09, 0.09, 0.095, 0.10, 0.105, 0.11,
                    0.115, 0.12, 0.125, 0.13, 0.135, 0.14, 0.135, 0.13,
                    0.125, 0.12, 0.115, 0.11, 0.105, 0.10, 0.10, 0.10,
                ]

            prices = (base_prices * ((hours // 24) + 1))[:hours]
            prices = [p * price_multiplier + np.random.uniform(-0.005, 0.005) for p in prices]

            df = pd.DataFrame({"timestamp": timestamps, "price_per_kwh": prices}).set_index("timestamp")
            self.registry.set("bess:grid_prices", df)

            min_price = df["price_per_kwh"].min()
            max_price = df["price_per_kwh"].max()
            spread = max_price - min_price

            return (
                f"Loaded grid prices ({source}) | "
                f"Min: ${min_price:.3f}/kWh | Max: ${max_price:.3f}/kWh | "
                f"Spread: ${spread:.3f}/kWh | Hours: {hours}"
            )
        except Exception as e:
            return f"Error loading grid prices: {str(e)}"


class BESSAnalyzer:
    def __init__(self, registry: SharedRegistry):
        self.registry = registry

    @property
    def specs(self) -> Optional[dict]:
        return self.registry.get("bess:specs")

    @property
    def load_profile(self) -> Optional[pd.DataFrame]:
        return self.registry.get("bess:load_profile")

    @property
    def solar_profile(self) -> Optional[pd.DataFrame]:
        return self.registry.get("bess:solar_profile")

    @property
    def tariff(self) -> Optional[dict]:
        return self.registry.get("bess:tariff")

    @agent_tool
    def get_profile_statistics(
        self,
        profile_type: Literal["load", "solar", "net_load"] = "load",
        include_hourly_breakdown: bool = False,
        percentile_threshold: float = 90.0,
    ) -> str:
        """
        Compute summary statistics for a loaded profile.

        Args:
            profile_type: Which profile to analyze: load, solar, or net_load (load minus solar).
            include_hourly_breakdown: If True, include percentile threshold and high-demand hour count.
            percentile_threshold: Percentile used for the high-demand hour breakdown.

        Returns:
            str: Peak, average, minimum, standard deviation, and total energy.
        """
        try:
            if profile_type == "load":
                if self.load_profile is None:
                    return "Error: No load profile loaded."
                df = self.load_profile
                col = "load_kw"
            elif profile_type == "solar":
                if self.solar_profile is None:
                    return "Error: No solar profile loaded."
                df = self.solar_profile
                col = "solar_kw"
            else:
                if self.load_profile is None or self.solar_profile is None:
                    return "Error: Both load and solar profiles required for net load."
                load = self.load_profile["load_kw"].values
                solar = self.solar_profile["solar_kw"].values
                min_len = min(len(load), len(solar))
                net = load[:min_len] - solar[:min_len]
                df = pd.DataFrame({"net_load_kw": net}, index=self.load_profile.index[:min_len])
                col = "net_load_kw"

            peak = df[col].max()
            avg = df[col].mean()
            min_val = df[col].min()
            total = df[col].sum()
            std = df[col].std()

            result = (
                f"{profile_type.upper()} Statistics:\n"
                f"  Peak: {peak:.2f} kW\n"
                f"  Average: {avg:.2f} kW\n"
                f"  Minimum: {min_val:.2f} kW\n"
                f"  Std Dev: {std:.2f} kW\n"
                f"  Total Energy: {total:.2f} kWh\n"
            )

            if include_hourly_breakdown:
                threshold = np.percentile(df[col].values, percentile_threshold)
                high_hours = df[df[col] >= threshold]
                result += (
                    f"  P{percentile_threshold:.0f} Threshold: {threshold:.2f} kW\n"
                    f"  High-Demand Hours: {len(high_hours)}"
                )

            return result
        except Exception as e:
            return f"Error calculating statistics: {str(e)}"

    @agent_tool
    def analyze_self_consumption(
        self,
        include_export_analysis: bool = True,
        target_self_consumption: Optional[float] = None,
    ) -> str:
        """
        Analyze solar self-consumption for loaded profiles.

        Args:
            include_export_analysis: If True, report excess solar exported and unmet load from the grid.
            target_self_consumption: Optional target ratio (0-1). Shows additional BESS capacity needed to reach it.

        Returns:
            str: Total load, total solar, self-consumed energy, and current self-consumption ratio.
        """
        if self.load_profile is None or self.solar_profile is None:
            return "Error: Both load and solar profiles must be loaded."

        try:
            load = self.load_profile["load_kw"].values
            solar = self.solar_profile["solar_kw"].values
            min_len = min(len(load), len(solar))
            load = load[:min_len]
            solar = solar[:min_len]

            self_consumed = np.minimum(solar, load).sum()
            total_solar = solar.sum()
            total_load = load.sum()

            if total_solar == 0:
                return "Error: Total solar generation is zero."

            current_ratio = self_consumed / total_solar
            excess_solar = np.maximum(solar - load, 0).sum()
            unmet_load = np.maximum(load - solar, 0).sum()

            result = (
                f"Self-Consumption Analysis:\n"
                f"  Total Load: {total_load:.1f} kWh\n"
                f"  Total Solar: {total_solar:.1f} kWh\n"
                f"  Self-Consumed: {self_consumed:.1f} kWh\n"
                f"  Current Ratio: {current_ratio*100:.1f}%\n"
            )

            if include_export_analysis:
                result += (
                    f"  Excess Solar (Exported): {excess_solar:.1f} kWh\n"
                    f"  Unmet Load (Grid Import): {unmet_load:.1f} kWh\n"
                )

            if target_self_consumption is not None:
                if current_ratio >= target_self_consumption:
                    result += f"\n  Target ({target_self_consumption*100:.0f}%) already met."
                else:
                    needed = (target_self_consumption - current_ratio) * total_solar
                    estimated_bess = min(excess_solar, needed) * 1.2
                    result += (
                        f"\n  To reach {target_self_consumption*100:.0f}%:\n"
                        f"    Additional Solar to Store: {needed:.1f} kWh\n"
                        f"    Estimated BESS Capacity: {estimated_bess:.1f} kWh"
                    )

            return result
        except Exception as e:
            return f"Error analyzing self-consumption: {str(e)}"

    @agent_tool
    def estimate_bess_sizing(
        self,
        application: Literal["peak_shaving", "self_consumption", "backup", "arbitrage"] = "peak_shaving",
        target_peak_reduction_pct: float = 20.0,
        target_peak_kw: Optional[float] = None,
        target_self_consumption: float = 0.80,
        backup_load_kw: float = 50.0,
        backup_hours: float = 4.0,
        arbitrage_cycles_per_day: float = 1.0,
    ) -> str:
        """
        Estimate BESS size for a given application.

        Args:
            application: Sizing objective: peak_shaving, self_consumption, backup, or arbitrage.
            target_peak_reduction_pct: Desired peak demand reduction percentage for peak_shaving.
            target_peak_kw: Explicit target peak in kW (overrides target_peak_reduction_pct).
            target_self_consumption: Desired self-consumption ratio (0-1) for self_consumption mode.
            backup_load_kw: Critical load power in kW for backup sizing.
            backup_hours: Required backup duration in hours for backup sizing.
            arbitrage_cycles_per_day: Charge-discharge cycles per day for arbitrage sizing.

        Returns:
            str: Recommended capacity (kWh) and power rating (kW) for the chosen application.
        """
        try:
            if application == "peak_shaving":
                if self.load_profile is None:
                    return "Error: Load profile required for peak shaving sizing."

                peak = self.load_profile["load_kw"].max()
                if target_peak_kw is not None:
                    target_peak = target_peak_kw
                    target_peak_reduction_pct = max(0.0, (peak - target_peak) / peak * 100) if peak else 0.0
                else:
                    reduction = peak * (target_peak_reduction_pct / 100)
                    target_peak = peak - reduction

                excess = self.load_profile["load_kw"] - target_peak
                excess = excess.clip(lower=0)
                energy_needed = excess.sum()
                power_needed = excess.max()

                return (
                    f"Peak Shaving Sizing ({target_peak_reduction_pct:.0f}% reduction):\n"
                    f"  Current Peak: {peak:.1f} kW\n"
                    f"  Target Peak: {target_peak:.1f} kW\n"
                    f"  Required Power: {power_needed:.1f} kW\n"
                    f"  Required Capacity: {energy_needed:.1f} kWh\n"
                    f"  Recommended (with buffer): {energy_needed*1.2:.1f} kWh"
                )
            elif application == "self_consumption":
                if self.load_profile is None or self.solar_profile is None:
                    return "Error: Both load and solar profiles required."

                load = self.load_profile["load_kw"].values
                solar = self.solar_profile["solar_kw"].values
                min_len = min(len(load), len(solar))

                excess_solar = np.maximum(solar[:min_len] - load[:min_len], 0).sum()
                max_excess_power = np.maximum(solar[:min_len] - load[:min_len], 0).max()

                return (
                    f"Self-Consumption Sizing (Target: {target_self_consumption*100:.0f}%):\n"
                    f"  Excess Solar Available: {excess_solar:.1f} kWh\n"
                    f"  Max Charge Power Needed: {max_excess_power:.1f} kW\n"
                    f"  Recommended Capacity: {excess_solar*target_self_consumption:.1f} kWh"
                )
            elif application == "backup":
                capacity_needed = backup_load_kw * backup_hours
                usable_capacity = capacity_needed / 0.85

                return (
                    f"Backup Sizing:\n"
                    f"  Critical Load: {backup_load_kw:.1f} kW\n"
                    f"  Required Duration: {backup_hours:.1f} hours\n"
                    f"  Usable Capacity Needed: {capacity_needed:.1f} kWh\n"
                    f"  Total Capacity (85% usable): {usable_capacity:.1f} kWh\n"
                    f"  Required Power Rating: {backup_load_kw:.1f} kW"
                )
            else:
                if self.specs:
                    capacity = self.specs.get("capacity_kwh", 100)
                    power = self.specs.get("power_kw", 50)
                else:
                    capacity = 100
                    power = 50

                daily_throughput = capacity * arbitrage_cycles_per_day * 2

                return (
                    f"Arbitrage Sizing ({arbitrage_cycles_per_day:.1f} cycles/day):\n"
                    f"  Daily Throughput: {daily_throughput:.1f} kWh\n"
                    f"  Optimal C-Rate: {arbitrage_cycles_per_day * 2:.1f}C (power/capacity ratio)\n"
                    f"  For 100kWh: Need {100 * arbitrage_cycles_per_day * 2:.0f} kW power"
                )
        except Exception as e:
            return f"Error estimating sizing: {str(e)}"

    @agent_tool
    def calculate_electricity_bill(
        self,
        profile_type: Literal["original", "with_bess"] = "original",
        include_demand_breakdown: bool = True,
        custom_peak_kw: Optional[float] = None,
    ) -> str:
        """
        Calculate the electricity bill for a load profile.

        Args:
            profile_type: original uses the raw load profile; with_bess uses post-simulation grid_power.
            include_demand_breakdown: If True, include peak demand broken down by rate period.
            custom_peak_kw: Optional peak demand override for demand charge calculation.

        Returns:
            str: Energy charges, demand charge, fixed charge, and total bill.
        """
        if self.tariff is None:
            return "Error: No tariff loaded."

        try:
            if profile_type == "original":
                if self.load_profile is None:
                    return "Error: No load profile loaded."
                load_values = self.load_profile["load_kw"].values
            else:
                sim_results = self.registry.get("bess:simulation_results")
                if sim_results is None:
                    return "Error: Required simulation state is missing."
                load_values = sim_results.get("grid_power", np.array([]))
                load_values = np.maximum(load_values, 0)

            tariff = self.tariff
            hour_to_rate = {}
            for period_name, period_data in tariff.get("energy_rates", {}).items():
                hours = period_data.get("hours", [])
                rate = period_data.get("price_per_kwh", 0)
                if isinstance(hours, list):
                    for h in hours:
                        hour_to_rate[h] = rate

            energy_cost = 0.0
            for i, load in enumerate(load_values):
                hour = i % 24
                rate = hour_to_rate.get(hour, 0.10)
                energy_cost += max(0, load) * rate

            peak_demand = custom_peak_kw if custom_peak_kw is not None else max(load_values)
            demand_rate = tariff.get("demand_charge_per_kw", 0)
            demand_charge = peak_demand * demand_rate

            fixed_charge = tariff.get("fixed_monthly_charge", 0)
            total = energy_cost + demand_charge + fixed_charge

            result = (
                f"Electricity Bill ({tariff.get('name', 'Unknown')}) - {profile_type}:\n"
                f"  Energy Charges: ${energy_cost:.2f}\n"
                f"  Peak Demand: {peak_demand:.1f} kW\n"
                f"  Demand Charge: ${demand_charge:.2f}\n"
                f"  Fixed Charge: ${fixed_charge:.2f}\n"
                f"  TOTAL: ${total:.2f}\n"
            )

            if include_demand_breakdown and len(load_values) > 0:
                peaks_by_period = {}
                for period_name in tariff.get("energy_rates", {}).keys():
                    period_hours = tariff["energy_rates"][period_name].get("hours", [])
                    if isinstance(period_hours, list) and period_hours:
                        period_values = [
                            load_values[i]
                            for i in range(len(load_values))
                            if i % 24 in period_hours
                        ]
                        if period_values:
                            peaks_by_period[period_name] = max(period_values)

                if peaks_by_period:
                    result += "\n  Peak by Period:\n"
                    for period, pk in peaks_by_period.items():
                        result += f"    {period}: {pk:.1f} kW\n"

            return result
        except Exception as e:
            return f"Error calculating bill: {str(e)}"

    @agent_tool
    def estimate_backup_duration(
        self,
        critical_load_kw: float = 50.0,
        initial_soc: float = 1.0,
        min_soc: float = 0.10,
        include_load_shedding_options: bool = False,
    ) -> str:
        """
        Estimate battery backup duration for a critical load.

        Args:
            critical_load_kw: Power draw of the critical load in kW.
            initial_soc: Starting state of charge (0-1).
            min_soc: Minimum allowable state of charge before backup ends (0-1).
            include_load_shedding_options: If True, also show duration at 75%, 50%, and 25% of load.

        Returns:
            str: Usable capacity and estimated backup duration in hours.
        """
        if not self.specs:
            return "Error: No battery specs loaded."

        try:
            capacity = self.specs.get("capacity_kwh", 100)
            power_kw = self.specs.get("power_kw", 50)
            spec_min_soc = self.specs.get("min_soc", 0.10)

            effective_min_soc = max(min_soc, spec_min_soc)
            usable_soc = initial_soc - effective_min_soc
            usable_capacity = capacity * usable_soc

            if critical_load_kw > power_kw:
                return (
                    f"Error: Critical load ({critical_load_kw:.1f} kW) exceeds "
                    f"battery power rating ({power_kw:.1f} kW)."
                )

            if critical_load_kw <= 0:
                return "Error: Critical load must be positive."

            duration_hours = usable_capacity / critical_load_kw

            result = (
                f"Backup Duration Estimate:\n"
                f"  Battery: {capacity:.0f} kWh / {power_kw:.0f} kW\n"
                f"  Initial SOC: {initial_soc*100:.0f}%\n"
                f"  Usable Capacity: {usable_capacity:.1f} kWh\n"
                f"  Critical Load: {critical_load_kw:.1f} kW\n"
                f"  Backup Duration: {duration_hours:.1f} hours\n"
            )

            if include_load_shedding_options:
                result += "\n  Load Shedding Options:\n"
                for pct in [75, 50, 25]:
                    reduced_load = critical_load_kw * (pct / 100)
                    if reduced_load <= power_kw:
                        reduced_duration = usable_capacity / reduced_load
                        result += f"    At {pct}% load ({reduced_load:.0f} kW): {reduced_duration:.1f} hours\n"

            return result
        except Exception as e:
            return f"Error calculating backup: {str(e)}"

    @agent_tool
    def get_battery_summary(
        self,
        include_cost_info: bool = True,
        include_technical_specs: bool = True,
    ) -> str:
        """
        Show the loaded battery specification summary.

        Args:
            include_cost_info: If True, include capital cost and annual O&M estimates.
            include_technical_specs: If True, include chemistry, C-rate, SOC range, and cycle life.

        Returns:
            str: Battery name, technical specifications, and financial parameters.
        """
        if not self.specs:
            return "Error: Required battery spec state is missing."

        try:
            s = self.specs
            result = f"Battery: {s.get('name', 'Unknown')}\n"

            if include_technical_specs:
                result += (
                    f"  Chemistry: {s.get('chemistry', 'N/A')}\n"
                    f"  Capacity: {s.get('capacity_kwh', 0)} kWh\n"
                    f"  Power: {s.get('power_kw', 0)} kW\n"
                    f"  C-Rate: {s.get('power_kw', 0) / s.get('capacity_kwh', 1):.2f}C\n"
                    f"  Round-trip Efficiency: {s.get('roundtrip_efficiency', 0)*100:.0f}%\n"
                    f"  SOC Range: {s.get('min_soc', 0)*100:.0f}% - {s.get('max_soc', 1)*100:.0f}%\n"
                    f"  Cycle Life: {s.get('cycle_life', 'N/A')} cycles\n"
                    f"  Calendar Life: {s.get('calendar_life_years', 'N/A')} years\n"
                )

            if include_cost_info:
                cap = s.get("capacity_kwh", 100)
                cost_per_kwh = s.get("capital_cost_per_kwh", 0)
                om_per_kwh = s.get("om_cost_per_kwh_year", 0)
                total_capital = cap * cost_per_kwh
                annual_om = cap * om_per_kwh

                result += (
                    f"\n  Capital Cost: ${cost_per_kwh}/kWh (${total_capital:,.0f} total)\n"
                    f"  Annual O&M: ${om_per_kwh}/kWh/yr (${annual_om:,.0f}/year)\n"
                )

            return result
        except Exception as e:
            return f"Error getting battery summary: {str(e)}"


class BESSSimulator:
    def __init__(self, registry: SharedRegistry):
        self.registry = registry
        self.simulation_state = None
        self.simulation_results = None

    @property
    def specs(self) -> Optional[dict]:
        return self.registry.get("bess:specs")

    @property
    def load_profile(self) -> Optional[pd.DataFrame]:
        return self.registry.get("bess:load_profile")

    @property
    def solar_profile(self) -> Optional[pd.DataFrame]:
        return self.registry.get("bess:solar_profile")

    @property
    def tariff(self) -> Optional[dict]:
        return self.registry.get("bess:tariff")

    @property
    def grid_prices(self) -> Optional[pd.DataFrame]:
        return self.registry.get("bess:grid_prices")

    @agent_tool
    def configure_simulation(
        self,
        initial_soc: float = 0.50,
        strategy: Literal["peak_shaving", "arbitrage", "self_consumption", "time_of_use"] = "peak_shaving",
        target_peak_kw: Optional[float] = None,
        charge_hours: Optional[str] = None,
        discharge_hours: Optional[str] = None,
    ) -> str:
        """
        Configure the BESS simulation state.

        Args:
            initial_soc: Starting state of charge (0-1).
            strategy: Dispatch strategy: peak_shaving, arbitrage, self_consumption, or time_of_use.
            target_peak_kw: Target peak demand in kW for peak_shaving strategy.
            charge_hours: Comma-separated hours-of-day for charging in time_of_use strategy (e.g., '0,1,2,3').
            discharge_hours: Comma-separated hours-of-day for discharging in time_of_use strategy.

        Returns:
            str: Confirmation of configured strategy, initial SOC, and battery rating.
        """
        if not self.specs:
            return "Error: Required battery spec state is missing."

        capacity = self.specs.get("capacity_kwh", 100)
        min_soc = self.specs.get("min_soc", 0.1)
        max_soc = self.specs.get("max_soc", 0.95)

        initial_soc = max(min_soc, min(max_soc, initial_soc))

        charge_h = None
        discharge_h = None
        if charge_hours:
            charge_h = [int(h.strip()) for h in charge_hours.split(",")]
        if discharge_hours:
            discharge_h = [int(h.strip()) for h in discharge_hours.split(",")]

        self.simulation_state = {
            "initial_soc": initial_soc,
            "capacity_kwh": capacity,
            "min_soc": min_soc,
            "max_soc": max_soc,
            "power_kw": self.specs.get("power_kw", 50),
            "efficiency": self.specs.get("roundtrip_efficiency", 0.92),
            "strategy": strategy,
            "target_peak_kw": target_peak_kw,
            "charge_hours": charge_h,
            "discharge_hours": discharge_h,
        }

        msg = (
            f"Simulation Configured:\n"
            f"  Strategy: {strategy}\n"
            f"  Initial SOC: {initial_soc*100:.0f}%\n"
            f"  Battery: {capacity} kWh / {self.specs.get('power_kw', 50)} kW\n"
        )
        if strategy == "peak_shaving" and target_peak_kw:
            msg += f"  Target Peak: {target_peak_kw} kW\n"
        if strategy == "time_of_use":
            msg += f"  Charge Hours: {charge_h}\n  Discharge Hours: {discharge_h}\n"

        return msg

    @agent_tool
    def run_simulation(self, hours: Optional[int] = None, verbose: bool = False) -> str:
        """
        Run the hourly BESS dispatch simulation.

        Call configure_simulation before this tool. Results are stored in the shared registry.

        Args:
            hours: Optional limit on number of hours to simulate (defaults to full profile length).
            verbose: If True, include final, min, and max SOC in the output.

        Returns:
            str: Total discharge, total charge, equivalent cycles, and peak reduction summary.
        """
        if not self.simulation_state:
            return "Error: Required simulation state is missing."
        if self.load_profile is None:
            return "Error: No load profile loaded."

        try:
            r = self._dispatch(self.simulation_state, hours)
            self.simulation_results = r
            self.registry.set("bess:simulation_results", r)

            power, grid_power, net_load, soc = r["power"], r["grid_power"], r["net_load"], r["soc"]
            capacity = self.simulation_state["capacity_kwh"]
            strategy = self.simulation_state["strategy"]
            total_discharge = power[power > 0].sum()
            total_charge = -power[power < 0].sum()
            original_peak = net_load.max()
            new_peak = grid_power.max()
            cycles = (total_discharge + total_charge) / (2 * capacity)

            result = (
                f"Simulation Complete ({strategy}):\n"
                f"  Duration: {r['n_steps']} hours\n"
                f"  Total Discharged: {total_discharge:.1f} kWh\n"
                f"  Total Charged: {total_charge:.1f} kWh\n"
                f"  Equivalent Cycles: {cycles:.2f}\n"
                f"  Original Peak: {original_peak:.1f} kW\n"
                f"  New Peak: {new_peak:.1f} kW\n"
                f"  Peak Reduction: {original_peak - new_peak:.1f} kW ({(original_peak - new_peak) / original_peak * 100:.1f}%)\n"
            )
            if verbose:
                result += (
                    f"  Final SOC: {soc[-1]*100:.1f}%\n"
                    f"  Min SOC: {soc.min()*100:.1f}%\n"
                    f"  Max SOC: {soc.max()*100:.1f}%\n"
                )
            return result
        except Exception as e:
            return f"Error running simulation: {str(e)}"

    def _dispatch(self, state: dict, hours: Optional[int] = None) -> dict:
        load = self.load_profile["load_kw"].values.copy()
        if hours:
            load = load[:hours]

        solar = np.zeros_like(load)
        if self.solar_profile is not None:
            solar_vals = self.solar_profile["solar_kw"].values
            min_len = min(len(load), len(solar_vals))
            if hours:
                min_len = min(min_len, hours)
            solar[:min_len] = solar_vals[:min_len]

        net_load = load - solar
        n_steps = len(load)
        strategy = state["strategy"]

        soc = np.zeros(n_steps + 1)
        soc[0] = state["initial_soc"]
        power = np.zeros(n_steps)
        grid_power = np.zeros(n_steps)

        capacity = state["capacity_kwh"]
        min_soc = state["min_soc"]
        max_soc = state["max_soc"]
        max_power = state["power_kw"]
        eff = state["efficiency"] ** 0.5

        target_peak = state.get("target_peak_kw") or (net_load.max() * 0.7)
        charge_hours = state.get("charge_hours") or [0, 1, 2, 3, 4, 5]
        discharge_hours = state.get("discharge_hours") or [14, 15, 16, 17, 18, 19]

        prices = None
        avg_price = 0.0
        if self.grid_prices is not None:
            prices = self.grid_prices["price_per_kwh"].values
            avg_price = prices.mean()

        for t in range(n_steps):
            hour = t % 24

            if strategy == "peak_shaving":
                if net_load[t] > target_peak:
                    discharge_needed = net_load[t] - target_peak
                    discharge_possible = min(
                        discharge_needed, max_power, (soc[t] - min_soc) * capacity * eff,
                    )
                    power[t] = discharge_possible
                elif net_load[t] < target_peak * 0.5:
                    charge_possible = min(max_power, (max_soc - soc[t]) * capacity / eff)
                    power[t] = -charge_possible * 0.5
            elif strategy == "self_consumption":
                if net_load[t] < 0:
                    excess = -net_load[t]
                    charge_possible = min(excess, max_power, (max_soc - soc[t]) * capacity / eff)
                    power[t] = -charge_possible
                elif net_load[t] > 0:
                    deficit = net_load[t]
                    discharge_possible = min(deficit, max_power, (soc[t] - min_soc) * capacity * eff)
                    power[t] = discharge_possible
            elif strategy == "arbitrage" and prices is not None:
                if t < len(prices):
                    if prices[t] < avg_price * 0.7:
                        charge_possible = min(max_power, (max_soc - soc[t]) * capacity / eff)
                        power[t] = -charge_possible
                    elif prices[t] > avg_price * 1.3:
                        discharge_possible = min(max_power, (soc[t] - min_soc) * capacity * eff)
                        power[t] = discharge_possible
            elif strategy == "time_of_use":
                if hour in charge_hours:
                    charge_possible = min(max_power, (max_soc - soc[t]) * capacity / eff)
                    power[t] = -charge_possible
                elif hour in discharge_hours:
                    discharge_possible = min(max_power, (soc[t] - min_soc) * capacity * eff)
                    power[t] = discharge_possible

            if power[t] > 0:
                soc[t + 1] = soc[t] - power[t] / (capacity * eff)
            else:
                soc[t + 1] = soc[t] - power[t] * eff / capacity

            soc[t + 1] = max(min_soc, min(max_soc, soc[t + 1]))
            grid_power[t] = net_load[t] - power[t]

        return {
            "soc": soc, "power": power, "grid_power": grid_power,
            "net_load": net_load, "original_load": load, "solar": solar, "n_steps": n_steps,
        }

    @agent_tool
    def get_simulation_results(
        self,
        metric: Literal["soc", "power", "grid_power", "summary"] = "summary",
        format_type: Literal["statistics", "hourly"] = "statistics",
    ) -> str:
        """
        Retrieve results from the latest BESS simulation.

        Args:
            metric: Which signal to report: soc, power, grid_power, or summary.
            format_type: statistics for aggregate stats or hourly for the first 12 time steps.

        Returns:
            str: Statistics or hourly sample for the selected metric.
        """
        if not self.simulation_results:
            return "Error: Required simulation state is missing."

        try:
            results = self.simulation_results

            if metric == "summary":
                power = results["power"]
                soc = results["soc"]
                grid = results["grid_power"]
                return (
                    f"Simulation Summary:\n"
                    f"  SOC - Initial: {soc[0]*100:.1f}%, Final: {soc[-1]*100:.1f}%, Range: {soc.min()*100:.1f}%-{soc.max()*100:.1f}%\n"
                    f"  Power - Discharge: {power[power > 0].sum():.1f} kWh, Charge: {-power[power < 0].sum():.1f} kWh\n"
                    f"  Grid - Peak Import: {grid.max():.1f} kW, Peak Export: {min(0, grid.min()):.1f} kW\n"
                )

            data = results.get(metric)
            if data is None:
                return f"Error: Metric '{metric}' not found."

            if format_type == "statistics":
                return (
                    f"{metric.upper()} Statistics:\n"
                    f"  Min: {data.min():.2f}\n"
                    f"  Max: {data.max():.2f}\n"
                    f"  Mean: {data.mean():.2f}\n"
                    f"  Std: {data.std():.2f}\n"
                )
            sample = data[: min(12, len(data))]
            lines = [f"  Hour {i}: {v:.2f}" for i, v in enumerate(sample)]
            return f"{metric.upper()} (first {len(sample)} hours):\n" + "\n".join(lines)
        except Exception as e:
            return f"Error getting results: {str(e)}"

    @agent_tool
    def calculate_savings(
        self,
        savings_type: Literal["total", "demand_only", "energy_only", "arbitrage"] = "total",
        annual_projection: bool = False,
    ) -> str:
        """
        Calculate savings from the latest BESS simulation.

        Args:
            savings_type: total, demand_only, energy_only, or arbitrage.
            annual_projection: If True, extrapolate the simulation period savings to a full year.

        Returns:
            str: Demand savings, energy savings, and total for the simulation period.
        """
        if not self.simulation_results:
            return "Error: No simulation results."

        try:
            results = self.simulation_results
            power = results["power"]
            grid = results["grid_power"]
            original_load = results["original_load"]
            net_load = results["net_load"]
            n_steps = results["n_steps"]

            days = n_steps / 24

            original_peak = net_load.max()
            new_peak = max(0, grid.max())
            demand_rate = self.tariff.get("demand_charge_per_kw", 15) if self.tariff else 15
            demand_savings = (original_peak - new_peak) * demand_rate

            energy_savings = 0
            if self.tariff:
                hour_to_rate = {}
                for period_name, period_data in self.tariff.get("energy_rates", {}).items():
                    hours = period_data.get("hours", [])
                    rate = period_data.get("price_per_kwh", 0)
                    if isinstance(hours, list):
                        for h in hours:
                            hour_to_rate[h] = rate

                for t in range(n_steps):
                    rate = hour_to_rate.get(t % 24, 0.10)
                    old_cost = max(0, net_load[t]) * rate
                    new_cost = max(0, grid[t]) * rate
                    energy_savings += old_cost - new_cost

            arb_revenue = 0
            arb_cost = 0
            if self.grid_prices is not None:
                prices = self.grid_prices["price_per_kwh"].values
                for t in range(min(n_steps, len(prices))):
                    if power[t] > 0:
                        arb_revenue += power[t] * prices[t]
                    elif power[t] < 0:
                        arb_cost += -power[t] * prices[t]

            total = demand_savings + energy_savings

            if savings_type == "demand_only":
                result = (
                    f"Demand Charge Savings:\n"
                    f"  Original Peak: {original_peak:.1f} kW\n"
                    f"  New Peak: {new_peak:.1f} kW\n"
                    f"  Rate: ${demand_rate:.2f}/kW\n"
                    f"  Monthly Savings: ${demand_savings:.2f}\n"
                )
            elif savings_type == "energy_only":
                result = f"Energy Savings: ${energy_savings:.2f}\n"
            elif savings_type == "arbitrage":
                result = (
                    f"Arbitrage Analysis:\n"
                    f"  Revenue (Selling): ${arb_revenue:.2f}\n"
                    f"  Cost (Buying): ${arb_cost:.2f}\n"
                    f"  Net Profit: ${arb_revenue - arb_cost:.2f}\n"
                )
            else:
                result = (
                    f"Total Savings:\n"
                    f"  Demand Savings: ${demand_savings:.2f}\n"
                    f"  Energy Savings: ${energy_savings:.2f}\n"
                    f"  Total: ${total:.2f}\n"
                )

            if annual_projection and days > 0:
                annual_factor = 365 / days
                annual = total * annual_factor
                result += f"\n  Annual Projection: ${annual:,.0f}/year\n"

            return result
        except Exception as e:
            return f"Error calculating savings: {str(e)}"

    @agent_tool
    def compare_strategies(
        self,
        strategies: str = "peak_shaving,self_consumption,time_of_use",
        metric: Literal["peak_reduction", "energy_savings", "cycles"] = "peak_reduction",
    ) -> str:
        """
        Compare BESS dispatch strategies.

        Args:
            strategies: Comma-separated strategy names (e.g., 'peak_shaving,self_consumption,time_of_use').
            metric: Sort criterion for the comparison: peak_reduction, energy_savings, or cycles.

        Returns:
            str: Ranked strategy comparison showing peak reduction and equivalent cycles per strategy.
        """
        if not self.specs or self.load_profile is None:
            return "Error: Battery specs and load profile required."

        try:
            strategy_list = [s.strip() for s in strategies.split(",")]
            results = []
            capacity = self.specs.get("capacity_kwh", 100)
            base_state = {
                "initial_soc": 0.5,
                "capacity_kwh": capacity,
                "min_soc": self.specs.get("min_soc", 0.1),
                "max_soc": self.specs.get("max_soc", 0.95),
                "power_kw": self.specs.get("power_kw", 50),
                "efficiency": self.specs.get("roundtrip_efficiency", 0.92),
                "target_peak_kw": self.load_profile["load_kw"].max() * 0.7,
                "charge_hours": None,
                "discharge_hours": None,
            }

            for strat in strategy_list:
                state = {**base_state, "strategy": strat}
                r = self._dispatch(state)
                peak_red = r["net_load"].max() - max(0, r["grid_power"].max())
                total_cycles = (
                    r["power"][r["power"] > 0].sum() + -r["power"][r["power"] < 0].sum()
                ) / (2 * capacity)
                results.append({"strategy": strat, "peak_reduction": peak_red, "cycles": total_cycles})

            output = f"Strategy Comparison ({metric}):\n"
            output += "-" * 50 + "\n"
            for r in sorted(results, key=lambda x: x.get(metric, 0), reverse=True):
                output += (
                    f"  {r['strategy']}: "
                    f"Peak Reduction: {r['peak_reduction']:.1f} kW, "
                    f"Cycles: {r['cycles']:.2f}\n"
                )

            return output
        except Exception as e:
            return f"Error comparing strategies: {str(e)}"

    def export_simulation_data(
        self,
        output_format: Literal["summary", "csv_path", "dict"] = "summary",
        include_metrics: bool = True,
    ) -> str:
        """
        Export the most recent BESS simulation results to a file or return a formatted summary.

        Args:
            output_format: summary for a text block, csv_path to write a timestamped CSV, or dict for array shapes.
            include_metrics: If True, include key performance metrics in the output.

        Returns:
            str: Export summary, written file path, or data shape information.
        """
        if not self.simulation_results:
            return "Error: No simulation results to export."

        try:
            r = self.simulation_results

            if output_format == "summary":
                output = "=== BESS Simulation Export ===\n"
                output += f"Duration: {r['n_steps']} hours\n"
                output += f"SOC Range: {r['soc'].min()*100:.1f}% - {r['soc'].max()*100:.1f}%\n"
                output += f"Total Discharge: {r['power'][r['power'] > 0].sum():.1f} kWh\n"
                output += f"Total Charge: {-r['power'][r['power'] < 0].sum():.1f} kWh\n"
                output += f"Original Peak: {r['net_load'].max():.1f} kW\n"
                output += f"New Peak: {r['grid_power'].max():.1f} kW\n"
                return output
            elif output_format == "csv_path":
                output_path = config.EXECUTION_OUTPUT_DIR / "bess" / "bess_simulation_results.csv"
                os.makedirs(output_path.parent, exist_ok=True)

                df = pd.DataFrame({
                    "hour": range(r["n_steps"]),
                    "original_load_kw": r["original_load"],
                    "solar_kw": r["solar"],
                    "net_load_kw": r["net_load"],
                    "battery_power_kw": r["power"],
                    "grid_power_kw": r["grid_power"],
                    "soc_pct": r["soc"][:-1] * 100,
                })
                df.to_csv(output_path, index=False)
                return f"Exported simulation results to: {output_path}"
            else:
                return (
                    f"Simulation Data Keys:\n"
                    f"  soc: {len(r['soc'])} values\n"
                    f"  power: {len(r['power'])} values\n"
                    f"  grid_power: {len(r['grid_power'])} values\n"
                    f"  net_load: {len(r['net_load'])} values\n"
                    f"  original_load: {len(r['original_load'])} values\n"
                    f"  solar: {len(r['solar'])} values\n"
                )
        except Exception as e:
            return f"Error exporting data: {str(e)}"


class BESSOptimizer:
    def __init__(self, registry: SharedRegistry):
        self.registry = registry
        self.optimization_results = None

    @property
    def specs(self) -> Optional[dict]:
        return self.registry.get("bess:specs")

    @property
    def simulation_results(self) -> Optional[dict]:
        return self.registry.get("bess:simulation_results")

    @property
    def tariff(self) -> Optional[dict]:
        return self.registry.get("bess:tariff")

    @agent_tool
    def calculate_economics(
        self,
        analysis_type: Literal["npv", "payback", "lcoe", "roi"] = "npv",
        project_years: int = 10,
        discount_rate: float = 0.05,
        annual_savings_override: Optional[float] = None,
        include_degradation: bool = True,
        electricity_escalation_rate: float = 0.02,
    ) -> str:
        """
        Perform financial analysis of the BESS investment.

        Args:
            analysis_type: npv, payback, lcoe, or roi.
            project_years: Project lifetime in years.
            discount_rate: Annual discount rate (e.g., 0.05 for 5%).
            annual_savings_override: Optional fixed annual savings in $ (overrides simulation estimate).
            include_degradation: If True, apply battery capacity degradation to savings over time.
            electricity_escalation_rate: Annual electricity price escalation rate (e.g., 0.02 for 2%).

        Returns:
            str: Financial analysis result for the selected analysis type.
        """
        if not self.specs:
            return "Error: No battery specs loaded."

        try:
            capacity = self.specs.get("capacity_kwh", 100)
            cost_per_kwh = self.specs.get("capital_cost_per_kwh", 350)
            om_per_kwh = self.specs.get("om_cost_per_kwh_year", 5)
            cycle_life = self.specs.get("cycle_life", 4000)

            capital_cost = capacity * cost_per_kwh
            annual_om = capacity * om_per_kwh

            if annual_savings_override is not None:
                base_annual_savings = annual_savings_override
            elif self.simulation_results:
                power = self.simulation_results.get("power", np.array([]))
                daily_discharge = power[power > 0].sum() if len(power) > 0 else 0
                base_annual_savings = daily_discharge * 0.15 * 365
            else:
                base_annual_savings = capacity * 50

            cashflows = [-capital_cost]
            cumulative = -capital_cost
            payback_year = None

            for year in range(1, project_years + 1):
                degradation_factor = 1.0
                if include_degradation:
                    degradation_factor = max(0.7, 1 - (year / project_years) * 0.3)

                escalation_factor = (1 + electricity_escalation_rate) ** (year - 1)
                annual_savings = base_annual_savings * degradation_factor * escalation_factor
                net_cashflow = annual_savings - annual_om
                cashflows.append(net_cashflow)

                cumulative += net_cashflow
                if payback_year is None and cumulative >= 0:
                    payback_year = year

            npv = -capital_cost
            for year in range(1, project_years + 1):
                npv += cashflows[year] / ((1 + discount_rate) ** year)

            total_discharge = capacity * 0.8 * 365 * project_years
            total_cost = capital_cost + annual_om * project_years
            lcoe = total_cost / total_discharge if total_discharge > 0 else 0

            total_savings = sum(cashflows[1:])
            roi = (total_savings - capital_cost) / capital_cost * 100 if capital_cost > 0 else 0

            if analysis_type == "npv":
                result = (
                    f"NPV Analysis ({project_years} years, {discount_rate*100:.1f}% discount):\n"
                    f"  Capital Cost: ${capital_cost:,.0f}\n"
                    f"  Base Annual Savings: ${base_annual_savings:,.0f}\n"
                    f"  Annual O&M: ${annual_om:,.0f}\n"
                    f"  Electricity Escalation: {electricity_escalation_rate*100:.1f}%/year\n"
                    f"  Degradation Included: {include_degradation}\n"
                    f"  NPV: ${npv:,.0f}\n"
                    f"  {'VIABLE' if npv > 0 else 'NOT VIABLE'}"
                )
            elif analysis_type == "payback":
                result = (
                    f"Payback Analysis:\n"
                    f"  Capital Cost: ${capital_cost:,.0f}\n"
                    f"  Average Annual Savings: ${sum(cashflows[1:]) / project_years:,.0f}\n"
                    f"  Simple Payback: {payback_year if payback_year else 'Never'} years\n"
                )
            elif analysis_type == "lcoe":
                result = (
                    f"LCOE Analysis:\n"
                    f"  Total Cost: ${total_cost:,.0f}\n"
                    f"  Estimated Lifetime Discharge: {total_discharge:,.0f} kWh\n"
                    f"  LCOE: ${lcoe:.4f}/kWh\n"
                )
            else:
                result = (
                    f"ROI Analysis:\n"
                    f"  Capital Cost: ${capital_cost:,.0f}\n"
                    f"  Total Savings: ${total_savings:,.0f}\n"
                    f"  Net Profit: ${total_savings - capital_cost:,.0f}\n"
                    f"  ROI: {roi:.1f}%\n"
                )
            self.registry.set("bess:economics_report", result)
            return result
        except Exception as e:
            return f"Error calculating economics: {str(e)}"

    @agent_tool
    def calculate_degradation(
        self,
        years: int = 10,
        cycles_per_day: Optional[float] = None,
        depth_of_discharge: float = 0.80,
        calendar_factor: float = 0.3,
    ) -> str:
        """
        Project battery state-of-health degradation over time.

        Args:
            years: Projection horizon in years.
            cycles_per_day: Optional override for daily cycle count (defaults to simulation result or 1.0).
            depth_of_discharge: Average depth of discharge per cycle (0-1).
            calendar_factor: Weight of calendar aging relative to cycle aging (0-1).

        Returns:
            str: Year-by-year SOH projection, equivalent cycle count, and final SOH.
        """
        if not self.specs:
            return "Error: No battery specs loaded."

        try:
            capacity = self.specs.get("capacity_kwh", 100)
            cycle_life = self.specs.get("cycle_life", 4000)
            calendar_life = self.specs.get("calendar_life_years", 15)

            if cycles_per_day is not None:
                daily_cycles = cycles_per_day
            elif self.simulation_results:
                power = np.array(self.simulation_results.get("power", []))
                daily_discharge = power[power > 0].sum() if len(power) > 0 else 0
                daily_cycles = daily_discharge / (capacity * depth_of_discharge)
            else:
                daily_cycles = 1.0

            annual_cycles = daily_cycles * 365
            total_cycles = annual_cycles * years
            equivalent_cycles = total_cycles * (depth_of_discharge / 0.8)

            cycle_soh_loss = min(1.0, equivalent_cycles / cycle_life)
            calendar_soh_loss = min(1.0, years / calendar_life)
            total_soh_loss = (1 - calendar_factor) * cycle_soh_loss + calendar_factor * calendar_soh_loss
            final_soh = max(0, 1 - total_soh_loss) * 100

            yearly_soh = []
            for y in range(1, min(years + 1, 6)):
                y_cycles = annual_cycles * y
                y_cycle_loss = min(1.0, y_cycles / cycle_life)
                y_cal_loss = min(1.0, y / calendar_life)
                y_total = max(0, 1 - ((1 - calendar_factor) * y_cycle_loss + calendar_factor * y_cal_loss)) * 100
                yearly_soh.append(f"    Year {y}: {y_total:.1f}%")

            result = (
                f"Degradation Analysis ({years} years):\n"
                f"  Daily Cycles: {daily_cycles:.2f}\n"
                f"  Annual Cycles: {annual_cycles:.0f}\n"
                f"  Total Cycles: {total_cycles:.0f}\n"
                f"  Equivalent Full Cycles: {equivalent_cycles:.0f} / {cycle_life}\n"
                f"  Average DOD: {depth_of_discharge*100:.0f}%\n"
                f"  Calendar Factor: {calendar_factor}\n"
                f"  Final SOH: {final_soh:.1f}%\n"
                f"\n  SOH Projection:\n" + "\n".join(yearly_soh)
            )
            self.registry.set("bess:degradation_report", result)
            return result
        except Exception as e:
            return f"Error calculating degradation: {str(e)}"

    @agent_tool
    def compare_battery_options(
        self,
        chemistries: str = "lfp_100kwh,nmc_100kwh",
        project_years: int = 10,
        comparison_metric: Literal["tco", "npv", "lcoe", "cycles"] = "tco",
        cycles_per_day: float = 1.0,
    ) -> str:
        """
        Compare battery options by cost and performance.

        Args:
            chemistries: Comma-separated battery spec names to compare (e.g., 'lfp_100kwh,nmc_100kwh').
            project_years: Project lifetime in years for TCO and NPV calculation.
            comparison_metric: Primary sort criterion: tco, npv, lcoe, or cycles.
            cycles_per_day: Assumed daily cycle rate for utilization calculation.

        Returns:
            str: Ranked comparison table with capital cost, TCO, NPV, and cycle utilization per chemistry.
        """
        try:
            bess_dir = config.INPUT_DIR / "bess" / "battery_specs"
            chemistry_list = [c.strip() for c in chemistries.split(",")]
            results = []

            for chem in chemistry_list:
                path = bess_dir / f"{chem}.json"
                if not path.exists():
                    continue

                with open(path) as f:
                    spec = json.load(f)

                cap = spec.get("capacity_kwh", 100)
                capital = cap * spec.get("capital_cost_per_kwh", 300)
                om_annual = cap * spec.get("om_cost_per_kwh_year", 5)
                tco = capital + om_annual * project_years

                total_cycles = cycles_per_day * 365 * project_years
                cycle_life = spec.get("cycle_life", 4000)
                cycle_utilization = min(1.0, total_cycles / cycle_life)

                annual_savings = cap * 50
                npv = -capital
                for y in range(1, project_years + 1):
                    npv += (annual_savings - om_annual) / (1.05 ** y)

                results.append({
                    "name": spec.get("name", chem),
                    "chemistry": spec.get("chemistry", "Unknown"),
                    "capacity": cap,
                    "efficiency": spec.get("roundtrip_efficiency", 0.9) * 100,
                    "cycle_life": cycle_life,
                    "capital": capital,
                    "tco": tco,
                    "npv": npv,
                    "cycle_utilization": cycle_utilization * 100,
                })

            if not results:
                return "Error: No valid battery specs found."

            sort_key = comparison_metric if comparison_metric in ["tco", "npv"] else "tco"
            reverse = comparison_metric == "npv"
            results.sort(key=lambda x: x.get(sort_key, 0), reverse=reverse)

            output = f"Battery Comparison ({comparison_metric.upper()}, {project_years} years):\n"
            output += "=" * 60 + "\n"

            for i, r in enumerate(results, 1):
                output += (
                    f"\n{i}. {r['name']}\n"
                    f"   Chemistry: {r['chemistry']} | Capacity: {r['capacity']} kWh\n"
                    f"   Efficiency: {r['efficiency']:.0f}% | Cycle Life: {r['cycle_life']}\n"
                    f"   Capital: ${r['capital']:,.0f} | TCO: ${r['tco']:,.0f}\n"
                    f"   NPV: ${r['npv']:,.0f} | Cycle Utilization: {r['cycle_utilization']:.0f}%\n"
                )

            return output
        except Exception as e:
            return f"Error comparing batteries: {str(e)}"

    @agent_tool
    def run_sensitivity_analysis(
        self,
        parameter: Literal["capacity", "electricity_price", "discount_rate", "cycles_per_day"] = "electricity_price",
        variations_pct: str = "-20,-10,0,10,20",
        base_metric: Literal["npv", "payback", "roi"] = "npv",
    ) -> str:
        """
        Run a sensitivity analysis on a key parameter.

        Args:
            parameter: Input parameter to vary: capacity, electricity_price, discount_rate, or cycles_per_day.
            variations_pct: Comma-separated percentage deviations to test (e.g., '-20,-10,0,10,20').
            base_metric: Financial metric to report at each variation: npv, payback, or roi.

        Returns:
            str: Table showing the financial metric value at each parameter variation.
        """
        if not self.specs:
            return "Error: No battery specs loaded."

        try:
            variations = [float(v.strip()) for v in variations_pct.split(",")]

            capacity = self.specs.get("capacity_kwh", 100)
            cost_per_kwh = self.specs.get("capital_cost_per_kwh", 350)
            om_per_kwh = self.specs.get("om_cost_per_kwh_year", 5)

            base_savings = capacity * 50
            base_discount = 0.05
            base_cycles = 1.0

            results = []

            for var_pct in variations:
                mult = 1 + (var_pct / 100)

                if parameter == "capacity":
                    var_capacity = capacity * mult
                    capital = var_capacity * cost_per_kwh
                    annual_savings = var_capacity * 50
                    discount = base_discount
                elif parameter == "electricity_price":
                    var_capacity = capacity
                    capital = var_capacity * cost_per_kwh
                    annual_savings = base_savings * mult
                    discount = base_discount
                elif parameter == "discount_rate":
                    var_capacity = capacity
                    capital = var_capacity * cost_per_kwh
                    annual_savings = base_savings
                    discount = base_discount * mult
                else:
                    var_capacity = capacity
                    capital = var_capacity * cost_per_kwh
                    annual_savings = base_savings * mult
                    discount = base_discount

                annual_om = var_capacity * om_per_kwh

                npv = -capital
                cumulative = -capital
                payback = None
                for y in range(1, 11):
                    cashflow = annual_savings - annual_om
                    npv += cashflow / ((1 + discount) ** y)
                    cumulative += cashflow
                    if payback is None and cumulative >= 0:
                        payback = y

                roi = ((annual_savings - annual_om) * 10 - capital) / capital * 100 if capital > 0 else 0

                if base_metric == "npv":
                    metric_value = f"${npv:,.0f}"
                elif base_metric == "payback":
                    metric_value = f"{payback if payback else 'N/A'} yrs"
                else:
                    metric_value = f"{roi:.1f}%"

                results.append(f"  {var_pct:+.0f}%: {metric_value}")

            result = (
                f"Sensitivity Analysis: {parameter} vs {base_metric.upper()}\n"
                f"{'=' * 40}\n" + "\n".join(results)
            )
            self.registry.set("bess:sensitivity_report", result)
            return result
        except Exception as e:
            return f"Error in sensitivity analysis: {str(e)}"

    @agent_tool
    def generate_investment_report(
        self,
        include_sensitivity: bool = True,
        include_degradation: bool = True,
        project_years: int = 10,
    ) -> str:
        """
        Generate a BESS investment analysis report.

        Args:
            include_sensitivity: If True, append a sensitivity analysis section.
            include_degradation: If True, append a degradation projection section.
            project_years: Project lifetime in years used for all financial sections.

        Returns:
            str: Formatted multi-section investment report covering specs, simulation, NPV, degradation, and sensitivity.
        """
        try:
            report = "=" * 60 + "\n"
            report += "    BESS INVESTMENT ANALYSIS REPORT\n"
            report += "=" * 60 + "\n\n"

            if self.specs:
                s = self.specs
                cap = s.get("capacity_kwh", 100)
                capital = cap * s.get("capital_cost_per_kwh", 350)

                report += "1. BATTERY SPECIFICATION\n"
                report += f"   {s.get('name', 'Unknown')} | {cap} kWh / {s.get('power_kw', 50)} kW\n"
                report += f"   Chemistry: {s.get('chemistry', 'N/A')} | Efficiency: {s.get('roundtrip_efficiency', 0.9)*100:.0f}%\n"
                report += f"   Capital Cost: ${capital:,.0f}\n\n"
            else:
                report += "1. BATTERY: Not loaded\n\n"

            if self.simulation_results:
                r = self.simulation_results
                orig_peak = r["net_load"].max()
                new_peak = max(0, r["grid_power"].max())
                report += "2. SIMULATION RESULTS\n"
                report += f"   Original Peak: {orig_peak:.1f} kW → New Peak: {new_peak:.1f} kW\n"
                report += f"   Peak Reduction: {orig_peak - new_peak:.1f} kW ({(orig_peak - new_peak) / orig_peak * 100:.1f}%)\n\n"
            else:
                report += "2. SIMULATION: Not run\n\n"

            report += f"3. FINANCIAL ANALYSIS ({project_years} years)\n"
            econ_cached = self.registry.get("bess:economics_report")
            if econ_cached:
                for line in econ_cached.split("\n")[1:]:
                    report += f"   {line}\n"
            else:
                report += "   Not computed.\n"
            report += "\n"

            if include_degradation:
                report += "4. DEGRADATION PROJECTION\n"
                deg_cached = self.registry.get("bess:degradation_report")
                if deg_cached:
                    for line in deg_cached.split("\n")[1:6]:
                        report += f"   {line}\n"
                else:
                    report += "   Not computed.\n"
                report += "\n"

            if include_sensitivity:
                report += "5. SENSITIVITY ANALYSIS\n"
                sens_cached = self.registry.get("bess:sensitivity_report")
                if sens_cached:
                    for line in sens_cached.split("\n")[1:]:
                        report += f"   {line}\n"
                else:
                    report += "   Not computed.\n"
                report += "\n"

            report += "=" * 60 + "\n"
            report += "    END OF REPORT\n"
            report += "=" * 60 + "\n"

            return report
        except Exception as e:
            return f"Error generating report: {str(e)}"

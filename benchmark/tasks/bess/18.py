from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader, BESSAnalyzer, BESSSimulator, BESSOptimizer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)
    simulator = BESSSimulator(registry)
    optimizer = BESSOptimizer(registry)

    print(loader.load_load_profile(profile_name="residential_home"))
    print(loader.load_solar_profile(profile_name="50kw_array",
          scale_factor=0.2, cloud_cover_factor=0.9))
    print(analyzer.get_profile_statistics(profile_type="net_load",
          include_hourly_breakdown=True, percentile_threshold=90.0))
    print(analyzer.analyze_self_consumption(
          include_export_analysis=True, target_self_consumption=0.85))
    print(analyzer.estimate_bess_sizing(
          application="backup", backup_load_kw=5.0, backup_hours=8.0))
    print(loader.load_battery_specs(spec_name="lfp_100kwh",
          capacity_override_kwh=40, power_override_kw=5))
    print(loader.load_tariff_structure(
          tariff_name="tou_summer", demand_charge_override=8.0))
    print(simulator.configure_simulation(initial_soc=0.5, strategy="self_consumption"))
    print(simulator.run_simulation(verbose=True))
    print(simulator.calculate_savings(savings_type="total", annual_projection=True))
    print(analyzer.estimate_backup_duration(critical_load_kw=5.0,
          initial_soc=1.0, min_soc=0.10, include_load_shedding_options=True))
    print(optimizer.calculate_economics(analysis_type="npv", project_years=12,
          discount_rate=0.05, include_degradation=True, electricity_escalation_rate=0.02))
    print(optimizer.calculate_degradation(years=12, cycles_per_day=0.5,
          depth_of_discharge=0.8))
    print(optimizer.run_sensitivity_analysis(parameter="electricity_price",
          variations_pct="-20,-10,0,10,20", base_metric="npv"))
    print(optimizer.generate_investment_report(
          include_sensitivity=True, include_degradation=True, project_years=12))


if __name__ == "__main__":
    main()

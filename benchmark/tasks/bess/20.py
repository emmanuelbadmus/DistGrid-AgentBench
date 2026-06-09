from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader, BESSAnalyzer, BESSSimulator, BESSOptimizer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)
    simulator = BESSSimulator(registry)
    optimizer = BESSOptimizer(registry)

    print(loader.load_battery_specs(spec_name='lfp_100kwh', capacity_override_kwh=300, power_override_kw=150))
    print(loader.load_load_profile(profile_name='commercial_office', scale_factor=2.0))
    print(loader.load_solar_profile(profile_name='50kw_array', scale_factor=2.0, cloud_cover_factor=0.85))
    print(loader.load_tariff_structure(tariff_name='tou_summer', demand_charge_override=22.0))
    print(analyzer.get_profile_statistics(profile_type='net_load', include_hourly_breakdown=True, percentile_threshold=95.0))
    print(analyzer.estimate_bess_sizing(application='peak_shaving', target_peak_kw=220.0))
    print(analyzer.estimate_bess_sizing(application='backup', backup_load_kw=75.0, backup_hours=6.0))
    print(simulator.configure_simulation(initial_soc=0.65, strategy='peak_shaving', target_peak_kw=220.0))
    print(simulator.run_simulation(verbose=True))
    print(analyzer.calculate_electricity_bill(profile_type='original', include_demand_breakdown=True))
    print(analyzer.calculate_electricity_bill(profile_type='with_bess', include_demand_breakdown=True))
    print(optimizer.calculate_degradation(years=15, cycles_per_day=1.2, depth_of_discharge=0.8))
    print(optimizer.calculate_economics(analysis_type='npv', project_years=12, discount_rate=0.06, include_degradation=True, electricity_escalation_rate=0.03))
    print(optimizer.run_sensitivity_analysis(parameter='electricity_price', variations_pct='-17.5,0,17.5', base_metric='npv'))


if __name__ == "__main__":
    main()

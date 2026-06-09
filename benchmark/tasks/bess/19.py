from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader, BESSAnalyzer, BESSSimulator, BESSOptimizer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)
    simulator = BESSSimulator(registry)
    optimizer = BESSOptimizer(registry)

    print(loader.load_battery_specs(spec_name='nmc_100kwh', power_override_kw=120))
    print(loader.load_load_profile(profile_name='commercial_office', scale_factor=1.5))
    print(loader.load_solar_profile(profile_name='50kw_array', scale_factor=1.5, cloud_cover_factor=0.9))
    print(loader.load_grid_prices(source='volatile', price_multiplier=1.6, hours=48))
    print(simulator.compare_strategies(strategies='peak_shaving,self_consumption,time_of_use,arbitrage', metric='energy_savings'))
    print(simulator.configure_simulation(initial_soc=0.45, strategy='arbitrage'))
    print(simulator.run_simulation(hours=48))
    print(simulator.get_simulation_results(metric='summary', format_type='statistics'))
    print(simulator.calculate_savings(savings_type='arbitrage', annual_projection=True))
    print(optimizer.calculate_degradation(years=10, cycles_per_day=2.0, depth_of_discharge=0.85))
    print(analyzer.estimate_backup_duration(critical_load_kw=50.0, initial_soc=0.9, min_soc=0.1, include_load_shedding_options=True))
    print(optimizer.compare_battery_options(chemistries='lfp_100kwh,nmc_100kwh', project_years=15, comparison_metric='npv', cycles_per_day=2.0))
    print(optimizer.generate_investment_report(include_sensitivity=True, include_degradation=True, project_years=10))


if __name__ == "__main__":
    main()

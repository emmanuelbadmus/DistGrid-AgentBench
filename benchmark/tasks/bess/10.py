from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader, BESSAnalyzer, BESSSimulator, BESSOptimizer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)
    simulator = BESSSimulator(registry)
    optimizer = BESSOptimizer(registry)

    print(loader.load_battery_specs(spec_name="nmc_100kwh"))
    print(loader.load_load_profile(profile_name="commercial_office"))
    print(loader.load_tariff_structure(tariff_name="tou_summer"))
    print(simulator.configure_simulation(initial_soc=0.40, strategy="arbitrage"))
    print(simulator.run_simulation(verbose=True))
    print(analyzer.calculate_electricity_bill(profile_type='original'))
    print(simulator.calculate_savings(savings_type="arbitrage", annual_projection=True))
    print(optimizer.calculate_degradation(years=10, cycles_per_day=1.0,
          depth_of_discharge=0.80, calendar_factor=0.15))
    print(optimizer.generate_investment_report(
          include_sensitivity=False, include_degradation=True, project_years=10))


if __name__ == "__main__":
    main()

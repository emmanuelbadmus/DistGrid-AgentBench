from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSAnalyzer
from distgrid_bench.tools.bess_analysis import BESSSimulator
from distgrid_bench.tools.bess_analysis import BESSOptimizer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)
    simulator = BESSSimulator(registry)
    optimizer = BESSOptimizer(registry)

    print(loader.load_battery_specs(spec_name="nmc_100kwh",
          capacity_override_kwh=100, power_override_kw=100))
    print(analyzer.get_battery_summary(
        include_cost_info=True, include_technical_specs=True))
    print(loader.load_load_profile(profile_name="commercial_office"))
    print(loader.load_grid_prices(
        source="volatile", price_multiplier=2.0, hours=24))
    print(simulator.configure_simulation(
        initial_soc=0.5, strategy="arbitrage"))
    print(simulator.run_simulation(verbose=True))
    print(optimizer.calculate_degradation(years=10, cycles_per_day=2.0,
          calendar_factor=0.2))
    print(optimizer.compare_battery_options(chemistries="lfp_100kwh,nmc_100kwh",
          project_years=10, comparison_metric="npv", cycles_per_day=2.0))


if __name__ == "__main__":
    main()

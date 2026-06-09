from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSSimulator


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    simulator = BESSSimulator(registry)

    print(loader.load_battery_specs(
        spec_name="nmc_100kwh", power_override_kw=100))
    print(loader.load_load_profile(profile_name="commercial_office"))
    print(loader.load_grid_prices(
        source="volatile", price_multiplier=1.5, hours=24))

    print(simulator.configure_simulation(
        initial_soc=0.5, strategy="arbitrage"))
    print(simulator.run_simulation(verbose=True))
    print(simulator.calculate_savings(
        savings_type="arbitrage", annual_projection=True))


if __name__ == "__main__":
    main()

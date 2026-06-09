from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader, BESSAnalyzer, BESSSimulator


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)
    simulator = BESSSimulator(registry)

    print(loader.load_battery_specs(spec_name="lfp_100kwh"))
    print(loader.load_load_profile(profile_name="commercial_office"))
    print(loader.load_tariff_structure(tariff_name="tou_summer"))

    print(simulator.configure_simulation(initial_soc=0.5,
          strategy="peak_shaving", target_peak_kw=130.0))
    print(simulator.run_simulation())
    print(simulator.get_simulation_results(metric="summary"))
    print(analyzer.calculate_electricity_bill(profile_type='original'))
    print(simulator.calculate_savings(
        savings_type="total", annual_projection=True))


if __name__ == "__main__":
    main()

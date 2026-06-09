from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSOptimizer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    optimizer = BESSOptimizer(registry)

    print(loader.load_battery_specs(spec_name="lfp_100kwh"))

    print(optimizer.compare_battery_options(chemistries="lfp_100kwh,nmc_100kwh",
          project_years=15, comparison_metric="tco", cycles_per_day=1.5))

    print(loader.load_battery_specs(spec_name="lfp_100kwh"))

    print(optimizer.calculate_degradation(
        years=15, cycles_per_day=1.5, depth_of_discharge=0.80))


if __name__ == "__main__":
    main()

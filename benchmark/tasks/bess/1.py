from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSAnalyzer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)

    print(loader.load_battery_specs(spec_name="lfp_100kwh",
          capacity_override_kwh=150, power_override_kw=75, efficiency_override=0.94))
    print(analyzer.get_battery_summary(
        include_cost_info=True, include_technical_specs=True))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSAnalyzer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)

    print(loader.load_battery_specs(spec_name="lfp_100kwh",
          capacity_override_kwh=500, power_override_kw=250))
    print(analyzer.get_battery_summary(
        include_cost_info=True, include_technical_specs=True))
    print(analyzer.estimate_backup_duration(critical_load_kw=200.0,
          initial_soc=1.0))
    print(analyzer.estimate_backup_duration(critical_load_kw=100.0,
          initial_soc=0.50))
    print(analyzer.estimate_backup_duration(critical_load_kw=25.0,
          initial_soc=1.0, min_soc=0.05, include_load_shedding_options=True))


if __name__ == "__main__":
    main()

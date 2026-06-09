from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSAnalyzer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)

    print(loader.load_battery_specs(spec_name="lfp_100kwh"))

    print(analyzer.estimate_backup_duration(critical_load_kw=40.0,
          initial_soc=0.95, min_soc=0.10, include_load_shedding_options=True))
    print(analyzer.estimate_backup_duration(critical_load_kw=40.0,
          initial_soc=0.70, min_soc=0.10, include_load_shedding_options=True))


if __name__ == "__main__":
    main()

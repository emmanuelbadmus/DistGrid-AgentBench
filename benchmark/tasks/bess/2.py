from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSAnalyzer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)

    print(loader.load_load_profile(profile_name="commercial_office",
          scale_factor=1.5, hours_to_load=24))
    print(analyzer.get_profile_statistics(profile_type="load",
          include_hourly_breakdown=True, percentile_threshold=90.0))


if __name__ == "__main__":
    main()

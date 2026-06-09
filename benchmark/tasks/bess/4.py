
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSAnalyzer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)

    print(loader.load_load_profile(profile_name="commercial_office"))
    print(loader.load_solar_profile(profile_name="50kw_array",
          scale_factor=2.0, cloud_cover_factor=0.8))

    print(analyzer.analyze_self_consumption(target_self_consumption=0.85))


if __name__ == "__main__":
    main()

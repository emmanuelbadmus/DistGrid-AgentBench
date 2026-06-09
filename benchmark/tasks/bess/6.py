from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSAnalyzer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)

    print(loader.load_load_profile(profile_name="commercial_office"))
    print(loader.load_solar_profile(profile_name="50kw_array"))

    print(analyzer.estimate_bess_sizing(
        application="peak_shaving", target_peak_reduction_pct=25.0))
    print(analyzer.estimate_bess_sizing(
        application="backup", backup_load_kw=60.0, backup_hours=4.0))
    print(analyzer.estimate_bess_sizing(
        application="self_consumption", target_self_consumption=0.90))


if __name__ == "__main__":
    main()

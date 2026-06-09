from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSAnalyzer
from distgrid_bench.tools.bess_analysis import BESSOptimizer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)
    optimizer = BESSOptimizer(registry)

    print(loader.load_load_profile(
        profile_name="commercial_office", scale_factor=1.5))
    print(loader.load_solar_profile(profile_name="50kw_array", scale_factor=1.5))
    print(loader.load_tariff_structure(tariff_name="tou_summer"))
    print(analyzer.get_profile_statistics(profile_type="net_load",
          include_hourly_breakdown=True, percentile_threshold=95.0))
    print(analyzer.analyze_self_consumption(
        include_export_analysis=True, target_self_consumption=0.90))
    print(analyzer.estimate_bess_sizing(
        application="peak_shaving", target_peak_reduction_pct=30.0))
    print(loader.load_battery_specs(
        spec_name="lfp_100kwh", capacity_override_kwh=150))
    print(analyzer.get_battery_summary(
        include_cost_info=True, include_technical_specs=True))
    print(optimizer.compare_battery_options(chemistries="lfp_100kwh,nmc_100kwh",
          project_years=10, comparison_metric="tco", cycles_per_day=1.0))


if __name__ == "__main__":
    main()

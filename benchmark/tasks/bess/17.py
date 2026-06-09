from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader
from distgrid_bench.tools.bess_analysis import BESSAnalyzer
from distgrid_bench.tools.bess_analysis import BESSSimulator
from distgrid_bench.tools.bess_analysis import BESSOptimizer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)
    simulator = BESSSimulator(registry)
    optimizer = BESSOptimizer(registry)

    print(loader.load_battery_specs(
        spec_name="lfp_100kwh", capacity_override_kwh=200))
    print(loader.load_load_profile(
        profile_name="commercial_office", scale_factor=2.0))
    print(loader.load_solar_profile(profile_name="50kw_array", scale_factor=2.0))
    print(loader.load_tariff_structure(tariff_name="tou_summer"))

    print(analyzer.calculate_electricity_bill(profile_type="original"))

    print(simulator.configure_simulation(initial_soc=0.5,
          strategy="peak_shaving", target_peak_kw=250.0))
    print(simulator.run_simulation(verbose=True))
    print(simulator.calculate_savings(
        savings_type="total", annual_projection=True))

    print(optimizer.calculate_economics(analysis_type="npv", project_years=10,
          discount_rate=0.06, include_degradation=True, electricity_escalation_rate=0.03))
    print(optimizer.run_sensitivity_analysis(parameter="electricity_price",
          variations_pct="-30,-15,0,15,30", base_metric="npv"))
    print(optimizer.generate_investment_report(
        include_sensitivity=True, include_degradation=True, project_years=10))


if __name__ == "__main__":
    main()

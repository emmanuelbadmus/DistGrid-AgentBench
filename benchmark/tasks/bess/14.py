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

    print(loader.load_battery_specs(spec_name="lfp_100kwh",
          capacity_override_kwh=200, power_override_kw=100))
    print(loader.load_load_profile(profile_name="commercial_office", scale_factor=2.0))
    print(loader.load_solar_profile(profile_name="50kw_array", scale_factor=2.0))
    print(analyzer.estimate_bess_sizing(
          application="peak_shaving", target_peak_kw=200.0))
    print(simulator.configure_simulation(initial_soc=0.5,
          strategy="peak_shaving", target_peak_kw=200.0))
    print(simulator.run_simulation())
    print(simulator.calculate_savings(savings_type="total", annual_projection=True))
    print(optimizer.run_sensitivity_analysis(parameter="electricity_price",
          variations_pct="-20,0,20,40"))
    print(optimizer.calculate_economics(analysis_type="npv", project_years=10,
          discount_rate=0.05, include_degradation=False,
          electricity_escalation_rate=0.02))


if __name__ == "__main__":
    main()

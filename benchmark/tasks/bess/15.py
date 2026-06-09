from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.bess_analysis import BESSLoader, BESSAnalyzer, BESSSimulator, BESSOptimizer


def main():
    registry = SharedRegistry()
    loader = BESSLoader(registry)
    analyzer = BESSAnalyzer(registry)
    simulator = BESSSimulator(registry)
    optimizer = BESSOptimizer(registry)

    print(loader.load_battery_specs(spec_name="lfp_100kwh",
          capacity_override_kwh=300, power_override_kw=150))
    print(loader.load_load_profile(profile_name="commercial_office", scale_factor=3.0))
    print(loader.load_solar_profile(profile_name="50kw_array", scale_factor=4.0))
    print(loader.load_tariff_structure(tariff_name="tou_summer",
          demand_charge_override=22.0, energy_rate_multiplier=1.15))
    print(analyzer.analyze_self_consumption(
          include_export_analysis=True, target_self_consumption=0.90))
    print(analyzer.calculate_electricity_bill(
          profile_type="original", include_demand_breakdown=True))
    print(simulator.configure_simulation(initial_soc=0.4, strategy="time_of_use",
          charge_hours="0,1,2,3,4,5,10,11,12", discharge_hours="16,17,18,19,20,21"))
    print(simulator.run_simulation(verbose=True))
    print(simulator.calculate_savings(savings_type="total", annual_projection=True))
    print(optimizer.calculate_economics(analysis_type="npv", project_years=12,
          discount_rate=0.07, include_degradation=True, electricity_escalation_rate=0.02))
    print(optimizer.calculate_degradation(years=12, cycles_per_day=1.5,
          depth_of_discharge=0.8))
    print(optimizer.run_sensitivity_analysis(parameter="electricity_price",
          variations_pct="-20,-10,0,10,20", base_metric="npv"))
    print(optimizer.generate_investment_report(
          include_sensitivity=True, include_degradation=True, project_years=12))


if __name__ == "__main__":
    main()

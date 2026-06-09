from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-22 17:00:00"))
    print(loader.load_solar(feeder="glover", timestamp="2025-03-22 17:00:00"))
    print(loader.load_distribution_network(feeder="glover"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_linf"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05, exception_bus_ids=None, exception_vmin_pu=None, exception_vmax_pu=None))
    print(simulator.set_cable_current_limits(rating_multiplier=1.13))
    print(simulator.build_objective(analysis_type="dhc_linf"))
    print(simulator.solve(solver="ipopt", tolerance=1e-6, max_iter=300))
    print(simulator.update_loads_curtailed_power(analysis_type="dhc_linf"))
    print(analyzer.list_top_buses(metric="curtailment", top_k=4))
    print(simulator.update_network_voltages())
    print(analyzer.check_voltage_violations())


if __name__ == "__main__":
    main()

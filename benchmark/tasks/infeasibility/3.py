from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-16 12:00:00"))
    print(loader.load_distribution_network(feeder="glover"))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="infeasibility_l2"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.97, default_vmax_pu=1.03))
    print(simulator.build_objective(analysis_type="infeasibility_l2"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=250))
    print(simulator.update_bus_infeasible_currents(analysis_type="infeasibility_l2"))
    print(analyzer.list_top_buses(metric="infeasibility", top_k=6))
    print(analyzer.check_voltage_violations())


if __name__ == "__main__":
    main()

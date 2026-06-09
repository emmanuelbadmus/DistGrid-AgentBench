from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-20 22:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-20 22:00:00"))
    print(loader.load_distribution_network(feeder="stowe"))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="infeasibility_l1"))
    print(simulator.set_cable_current_limits(rating_multiplier=1.10))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.10))
    print(simulator.build_objective(analysis_type="infeasibility_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=300))
    print(simulator.update_bus_infeasible_currents(analysis_type="infeasibility_l1"))
    print(simulator.update_network_voltages())
    print(analyzer.plot_network_data(plot_type="voltage", feeder="stowe"))
    print(analyzer.plot_network_data(plot_type="infeasibility", feeder="stowe"))


if __name__ == "__main__":
    main()

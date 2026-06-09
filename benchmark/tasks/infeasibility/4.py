from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-21 18:00:00"))
    print(loader.load_solar(feeder="glover", timestamp="2025-03-21 18:00:00"))
    print(loader.load_distribution_network(feeder="glover"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="infeasibility_l1"))
    print(simulator.build_objective(analysis_type="infeasibility_l1"))
    print(simulator.solve(tolerance=1e-6))
    print(simulator.update_bus_infeasible_currents(analysis_type="infeasibility_l1"))
    print(analyzer.list_top_buses(metric="infeasibility", top_k=5))
    print(simulator.update_network_voltages())
    print(analyzer.plot_network_data(plot_type="voltage", feeder="glover"))


if __name__ == "__main__":
    main()

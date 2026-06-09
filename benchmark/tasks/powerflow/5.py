from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="south_hero", timestamp="2025-03-17 19:00:00"))
    print(loader.load_solar(feeder="south_hero", timestamp="2025-03-17 19:00:00"))
    print(loader.load_distribution_network(feeder="south_hero"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="powerflow"))
    print(simulator.build_objective(analysis_type="powerflow"))
    print(simulator.solve())
    print(simulator.update_network_voltages())
    print(analyzer.get_bus_voltages(limit=20))


if __name__ == "__main__":
    main()

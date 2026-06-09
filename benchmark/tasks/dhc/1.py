from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="rochester", timestamp="2025-03-23 01:00:00"))
    print(loader.load_solar(feeder="rochester", timestamp="2025-03-23 01:00:00"))
    print(loader.load_distribution_network(feeder="rochester"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_linf"))
    print(simulator.build_objective(analysis_type="dhc_linf"))
    print(simulator.solve())
    print(simulator.update_network_voltages())


if __name__ == "__main__":
    main()

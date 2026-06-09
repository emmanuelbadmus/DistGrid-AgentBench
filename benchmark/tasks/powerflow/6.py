from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-21 09:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-21 09:00:00"))
    print(loader.load_distribution_network(feeder="stowe"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="powerflow"))
    print(simulator.build_objective(analysis_type="powerflow"))
    print(simulator.solve())
    print(simulator.update_network_voltages())
    print(analyzer.plot_network_data(plot_type="voltage", feeder="stowe"))


if __name__ == "__main__":
    main()

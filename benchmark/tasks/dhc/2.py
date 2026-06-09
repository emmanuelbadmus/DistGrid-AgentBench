from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-16 12:00:00"))
    print(loader.load_solar(feeder="glover", timestamp="2025-03-16 12:00:00"))
    print(loader.load_distribution_network(feeder="glover"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_l2"))
    print(simulator.build_objective(analysis_type="dhc_l2"))
    print(simulator.solve(tolerance=1e-2, max_iter=100))
    print(simulator.update_network_voltages())
    print(analyzer.export_data_to_file(export_type="voltages", file_format="csv"))


if __name__ == "__main__":
    main()

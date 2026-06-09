from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="rochester", timestamp="2025-03-22 14:00:00"))
    print(loader.load_solar(feeder="rochester", timestamp="2025-03-22 14:00:00"))
    print(loader.load_distribution_network(feeder="rochester"))
    print(simulator.create_and_initialize_model())
    print(simulator.set_transformer_loading_limits(rating_multiplier=0.95))
    print(simulator.build_constraints(analysis_type="powerflow"))
    print(simulator.build_objective(analysis_type="powerflow"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=200))
    print(simulator.update_network_voltages())
    print(analyzer.check_voltage_violations())
    print(analyzer.export_data_to_file(export_type="voltages", file_format="json"))


if __name__ == "__main__":
    main()

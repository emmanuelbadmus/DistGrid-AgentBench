from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="south_hero", timestamp="2025-03-18 19:00:00"))
    print(loader.load_solar(feeder="south_hero", timestamp="2025-03-18 19:00:00"))
    print(loader.load_distribution_network(feeder="south_hero"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_linf"))
    print(simulator.set_cable_current_limits(rating_multiplier=1.15))
    print(simulator.build_objective(analysis_type="dhc_linf"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=200))
    print(simulator.update_network_voltages())
    print(analyzer.export_data_to_file(export_type="voltages", file_format="csv"))
    print(analyzer.plot_network_data(plot_type="voltage", feeder="south_hero"))


if __name__ == "__main__":
    main()

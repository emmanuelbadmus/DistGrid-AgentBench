from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-21 10:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-21 10:00:00"))
    print(loader.load_distribution_network(feeder="stowe"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_linf"))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.05))
    print(simulator.build_objective(analysis_type="dhc_linf"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=150))
    print(simulator.update_loads_curtailed_power(analysis_type="dhc_linf"))
    print(simulator.update_network_voltages())
    print(analyzer.list_top_buses(metric="curtailment", top_k=5))
    print(analyzer.export_data_to_file(export_type="voltages", file_format="csv"))


if __name__ == "__main__":
    main()

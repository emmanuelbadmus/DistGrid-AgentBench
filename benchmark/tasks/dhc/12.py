from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="rochester", timestamp="2025-03-21 08:00:00"))
    print(loader.load_solar(feeder="rochester", timestamp="2025-03-21 08:00:00"))
    print(loader.load_distribution_network(feeder="rochester"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_linf"))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.09))
    print(simulator.set_cable_current_limits(rating_multiplier=1.09))
    print(simulator.build_objective(analysis_type="dhc_linf"))
    print(simulator.solve(solver="ipopt", tolerance=1e-6, max_iter=300))
    print(simulator.update_network_voltages())
    print(analyzer.plot_network_data(plot_type="voltage", feeder="rochester"))
    print(simulator.update_loads_curtailed_power(analysis_type="dhc_linf"))
    print(analyzer.list_top_buses(metric="curtailment", top_k=5))


if __name__ == "__main__":
    main()

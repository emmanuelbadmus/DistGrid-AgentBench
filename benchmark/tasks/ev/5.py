from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_ev_charger_data(feeder="rochester", demand_scale=0.75))
    print(loader.load_distribution_network(feeder="rochester"))
    print(simulator.create_and_initialize_model())
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.05))
    print(simulator.set_ev_charger_placement_targets(min_total_kw=150.0))
    print(simulator.build_constraints(analysis_type="ev_placement_l1", min_total_kw=150.0))
    print(simulator.build_objective(analysis_type="ev_placement_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-3, max_iter=1200))
    print(simulator.update_ev_charger_placement(min_served_kw=1e-3))
    print(analyzer.list_top_buses(metric="ev_unserved", top_k=5))
    print(analyzer.summarize_ev_charger_placement(top_k=7))


if __name__ == "__main__":
    main()

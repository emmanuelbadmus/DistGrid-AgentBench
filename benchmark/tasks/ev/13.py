from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="rochester", timestamp="2025-03-19T20:00:00"))
    print(loader.load_solar(feeder="rochester", timestamp="2025-03-19T20:00:00"))
    print(loader.load_ev_charger_data(feeder="rochester"))
    print(loader.load_distribution_network(feeder="rochester"))
    print(simulator.create_and_initialize_model())
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.05))
    print(simulator.set_ev_charger_placement_targets(max_chargers=5, min_total_kw=300.0))
    print(simulator.build_constraints(analysis_type="ev_placement_l1", max_chargers=5, min_total_kw=300.0))
    print(simulator.build_objective(analysis_type="ev_placement_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=3000))
    print(simulator.update_ev_charger_placement(min_served_kw=1e-3))
    print(analyzer.list_top_buses(metric="ev_served", top_k=5))


if __name__ == "__main__":
    main()

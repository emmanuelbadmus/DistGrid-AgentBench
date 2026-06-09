from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-21T18:00:00"))
    print(loader.load_solar(feeder="glover", timestamp="2025-03-21T18:00:00"))
    print(loader.load_ev_charger_data(feeder="glover", demand_scale=1.1))
    print(loader.load_distribution_network(feeder="glover"))
    print(simulator.create_and_initialize_model())
    print(simulator.set_cable_current_limits(rating_multiplier=1.05))
    print(simulator.set_ev_charger_placement_targets(max_chargers=2))
    print(simulator.build_constraints(analysis_type="ev_placement_l2", max_chargers=2))
    print(simulator.build_objective(analysis_type="ev_placement_l2"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=1500))
    print(simulator.update_ev_charger_placement(min_served_kw=1e-3))
    print(simulator.update_network_voltages())
    print(analyzer.list_top_buses(metric="ev_served", top_k=5))
    print(analyzer.plot_network_data(plot_type="ev_placement", feeder="glover"))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="south_hero", timestamp="2025-03-18T12:00:00"))
    print(loader.load_ev_charger_data(feeder="south_hero", demand_scale=0.85))
    print(loader.load_distribution_network(feeder="south_hero"))
    print(simulator.create_and_initialize_model())
    print(simulator.set_ev_charger_placement_targets(max_chargers=3, min_total_kw=180.0))
    print(simulator.build_constraints(analysis_type="ev_placement_l1", max_chargers=3, min_total_kw=180.0))
    print(simulator.build_objective(analysis_type="ev_placement_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=1200))
    print(simulator.update_ev_charger_placement(min_served_kw=1e-3))
    print(analyzer.export_data_to_file(export_type="ev_placement", file_format="json"))


if __name__ == "__main__":
    main()

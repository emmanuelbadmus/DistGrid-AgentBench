from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-19 19:00:00"))
    print(loader.load_solar(feeder="glover", timestamp="2025-03-19 19:00:00"))
    print(loader.load_ev_charger_data(feeder="glover", demand_scale=1.15))
    print(loader.load_distribution_network(feeder="glover"))
    print(simulator.create_and_initialize_model())
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05))
    print(simulator.set_cable_current_limits(rating_multiplier=1.12))
    print(simulator.set_ev_charger_placement_targets(max_chargers=4))
    print(simulator.build_constraints(analysis_type="ev_placement_l2", max_chargers=4))
    print(simulator.build_objective(analysis_type="ev_placement_l2"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=1500))
    print(simulator.update_ev_charger_placement(min_served_kw=1e-3))
    print(simulator.update_network_voltages())
    print(analyzer.plot_network_data(plot_type="ev_placement", feeder="glover"))
    print(analyzer.export_data_to_file(export_type="ev_placement", file_format="csv"))


if __name__ == "__main__":
    main()

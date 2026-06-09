from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-22T16:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-22T16:00:00"))
    print(loader.load_ev_charger_data(feeder="stowe"))
    print(loader.load_distribution_network(feeder="stowe"))
    print(simulator.create_and_initialize_model())
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.10))
    print(simulator.set_cable_current_limits(rating_multiplier=1.10))
    print(simulator.set_ev_charger_placement_targets(max_chargers=4, min_total_kw=220.0))
    print(simulator.build_constraints(analysis_type="ev_placement_l1", max_chargers=4, min_total_kw=220.0))
    print(simulator.build_objective(analysis_type="ev_placement_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=1800))
    print(simulator.update_ev_charger_placement(min_served_kw=1e-3))
    print(simulator.update_network_voltages())
    print(analyzer.export_data_to_file(export_type="voltages", file_format="json"))
    print(analyzer.export_data_to_file(export_type="ev_placement", file_format="csv"))
    print(analyzer.check_ev_charger_voltage_impacts(vmin_pu=0.95, vmax_pu=1.05))


if __name__ == "__main__":
    main()

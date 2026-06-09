from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder='south_hero', timestamp='2025-03-20 14:00:00'))
    print(loader.load_solar(feeder='south_hero', timestamp='2025-03-20 14:00:00'))
    print(loader.load_ev_charger_data(feeder='south_hero', demand_scale=1.25))
    print(loader.load_distribution_network(feeder='south_hero'))
    print(simulator.create_and_initialize_model())
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.05))
    print(simulator.set_cable_current_limits(rating_multiplier=1.08))
    print(simulator.set_ev_charger_placement_targets(max_chargers=5, min_total_kw=250.0))
    print(simulator.build_constraints(analysis_type='ev_placement_l1', max_chargers=5, min_total_kw=250.0))
    print(simulator.build_objective(analysis_type='ev_placement_l1'))
    print(simulator.solve(solver='ipopt', tolerance=0.0001, max_iter=2000))
    print(simulator.update_ev_charger_placement(min_served_kw=0.001))
    print(simulator.update_network_voltages())
    print(analyzer.summarize_ev_charger_placement(top_k=10))
    print(analyzer.check_ev_charger_voltage_impacts(vmin_pu=0.95, vmax_pu=1.05))
    print(analyzer.list_top_buses(metric='ev_unserved', top_k=6))
    print(analyzer.plot_network_data(plot_type='ev_placement', feeder='south_hero'))
    print(analyzer.export_data_to_file(export_type='ev_placement', file_format='csv'))
    print(analyzer.export_data_to_file(export_type='voltages', file_format='json'))


if __name__ == "__main__":
    main()

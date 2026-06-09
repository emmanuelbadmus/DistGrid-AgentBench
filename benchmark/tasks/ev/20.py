from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder='rochester', timestamp='2025-03-19 20:00:00'))
    print(loader.load_solar(feeder='rochester', timestamp='2025-03-19 20:00:00'))
    print(loader.load_ev_charger_data(feeder='rochester', demand_scale=1.1))
    print(analyzer.list_ev_charger_candidates(top_k=8, sort_by='demand'))
    print(loader.load_distribution_network(feeder='rochester'))
    print(simulator.create_and_initialize_model())
    print(simulator.set_voltage_limits(default_vmin_pu=0.96, default_vmax_pu=1.04))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.03))
    print(simulator.set_ev_charger_placement_targets(max_chargers=4, min_total_kw=275.0))
    print(simulator.build_constraints(analysis_type='ev_placement_l1', max_chargers=4, min_total_kw=275.0))
    print(simulator.build_objective(analysis_type='ev_placement_l1'))
    print(simulator.solve(solver='ipopt', tolerance=0.0001, max_iter=2200))
    print(simulator.update_ev_charger_placement(min_served_kw=0.001))
    print(simulator.update_network_voltages())
    print(analyzer.summarize_ev_charger_placement(top_k=8))
    print(analyzer.list_top_buses(metric='ev_served', top_k=5))
    print(analyzer.list_top_buses(metric='ev_unserved', top_k=5))
    print(analyzer.check_ev_charger_voltage_impacts(vmin_pu=0.96, vmax_pu=1.04))
    print(analyzer.plot_network_data(plot_type='ev_placement', feeder='rochester'))
    print(analyzer.export_data_to_file(export_type='ev_placement', file_format='json'))
    print(analyzer.export_data_to_file(export_type='voltages', file_format='csv'))


if __name__ == "__main__":
    main()

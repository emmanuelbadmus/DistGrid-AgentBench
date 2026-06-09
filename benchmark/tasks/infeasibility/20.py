from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder='south_hero', timestamp='2025-03-22 10:00:00'))
    print(loader.load_solar(feeder='south_hero', timestamp='2025-03-22 10:00:00'))
    print(loader.load_distribution_network(feeder='south_hero'))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type='infeasibility_l1'))
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05, exception_bus_ids=['8', '16', '24'], exception_vmin_pu=0.985, exception_vmax_pu=1.015))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.03))
    print(simulator.set_cable_current_limits(rating_multiplier=1.06))
    print(simulator.build_objective(analysis_type='infeasibility_l1'))
    print(simulator.solve(solver='ipopt', tolerance=1e-06, max_iter=700))
    print(simulator.update_bus_infeasible_currents(analysis_type='infeasibility_l1'))
    print(simulator.update_network_voltages())
    print(analyzer.list_top_buses(metric='infeasibility', top_k=12))
    print(analyzer.export_data_to_file(export_type='voltages', file_format='json'))
    print(analyzer.plot_network_data(plot_type='infeasibility', feeder='south_hero'))
    print(analyzer.plot_network_data(plot_type='voltage', feeder='south_hero'))
    print(analyzer.check_voltage_violations())


if __name__ == "__main__":
    main()

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
    print(loader.load_distribution_network(feeder='rochester'))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type='dhc_l2'))
    print(simulator.set_voltage_limits(default_vmin_pu=0.96, default_vmax_pu=1.04))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.05))
    print(simulator.set_cable_current_limits(rating_multiplier=1.05))
    print(simulator.build_objective(analysis_type='dhc_l2'))
    print(simulator.solve(solver='ipopt', tolerance=1e-06, max_iter=600))
    print(simulator.update_loads_curtailed_power(analysis_type='dhc_l2'))
    print(simulator.update_network_voltages())
    print(analyzer.list_top_buses(metric='curtailment', top_k=10))
    print(analyzer.plot_network_data(plot_type='curtailment', feeder='rochester'))
    print(analyzer.plot_network_data(plot_type='voltage', feeder='rochester'))
    print(analyzer.export_data_to_file(export_type='voltages', file_format='csv'))
    print(analyzer.check_voltage_violations())


if __name__ == "__main__":
    main()

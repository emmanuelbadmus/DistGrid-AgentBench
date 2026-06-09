from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder='stowe', timestamp='2025-03-23 10:00:00'))
    print(loader.load_solar(feeder='stowe', timestamp='2025-03-23 10:00:00'))
    print(loader.load_distribution_network(feeder='stowe'))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type='dhc_linf'))
    print(simulator.set_voltage_limits(default_vmin_pu=0.94, default_vmax_pu=1.06, exception_bus_ids=['10', '25', '36'], exception_vmin_pu=0.98, exception_vmax_pu=1.02))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.08))
    print(simulator.set_cable_current_limits(rating_multiplier=1.1))
    print(simulator.build_objective(analysis_type='dhc_linf'))
    print(simulator.solve(solver='ipopt', tolerance=1e-06, max_iter=800))
    print(simulator.update_loads_curtailed_power(analysis_type='dhc_linf'))
    print(simulator.update_network_voltages())
    print(analyzer.list_top_buses(metric='curtailment', top_k=12))
    print(analyzer.check_voltage_violations())
    print(analyzer.plot_network_data(plot_type='curtailment', feeder='stowe'))
    print(analyzer.plot_network_data(plot_type='voltage', feeder='stowe'))
    print(analyzer.export_data_to_file(export_type='voltages', file_format='json'))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder='south_hero', timestamp='2025-03-21 08:00:00'))
    print(loader.load_solar(feeder='south_hero', timestamp='2025-03-21 08:00:00'))
    print(loader.load_distribution_network(feeder='south_hero'))
    print(analyzer.calculate_total_power(power_type='load'))
    print(analyzer.calculate_total_power(power_type='solar'))
    print(simulator.create_and_initialize_model())
    print(simulator.set_voltage_limits(default_vmin_pu=0.97, default_vmax_pu=1.03))
    print(simulator.set_cable_current_limits(rating_multiplier=1.03))
    print(simulator.set_transformer_loading_limits(rating_multiplier=0.98))
    print(simulator.build_constraints(analysis_type='powerflow'))
    print(simulator.build_objective(analysis_type='powerflow'))
    print(simulator.solve(solver='ipopt', tolerance=1e-05, max_iter=400))
    print(simulator.update_network_voltages())
    print(analyzer.check_voltage_violations())
    print(analyzer.plot_network_data(plot_type='voltage', feeder='south_hero'))
    print(analyzer.export_data_to_file(export_type='voltages', file_format='csv'))


if __name__ == "__main__":
    main()

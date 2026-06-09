from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder='rochester', timestamp='2025-03-19 15:00:00'))
    print(loader.load_solar(feeder='rochester', timestamp='2025-03-19 15:00:00'))
    print(loader.load_distribution_network(feeder='rochester'))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type='infeasibility_l2'))
    print(simulator.set_voltage_limits(default_vmin_pu=0.94, default_vmax_pu=1.06, exception_bus_ids=['14', '32', '55'], exception_vmin_pu=0.98, exception_vmax_pu=1.02))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.05))
    print(simulator.set_cable_current_limits(rating_multiplier=1.08))
    print(simulator.build_objective(analysis_type='infeasibility_l2'))
    print(simulator.solve(solver='ipopt', tolerance=1e-06, max_iter=600))
    print(simulator.update_bus_infeasible_currents(analysis_type='infeasibility_l2'))
    print(simulator.update_network_voltages())
    print(analyzer.list_top_buses(metric='infeasibility', top_k=10))
    print(analyzer.export_data_to_file(export_type='voltages', file_format='csv'))


if __name__ == "__main__":
    main()

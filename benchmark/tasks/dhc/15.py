from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="rochester", timestamp="2025-03-20 06:00:00"))
    print(loader.load_solar(feeder="rochester", timestamp="2025-03-20 06:00:00"))
    print(loader.load_distribution_network(feeder="rochester"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_l1"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05, exception_bus_ids=None, exception_vmin_pu=None, exception_vmax_pu=None))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.08))
    print(simulator.build_objective(analysis_type="dhc_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=1000))
    print(simulator.update_loads_curtailed_power(analysis_type="dhc_l1"))
    print(analyzer.plot_network_data(plot_type="curtailment", feeder="rochester"))
    print(simulator.update_network_voltages())
    print(analyzer.export_data_to_file(export_type="voltages", file_format="json"))


if __name__ == "__main__":
    main()

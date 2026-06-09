from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-19 15:00:00"))
    print(loader.load_solar(feeder="glover", timestamp="2025-03-19 15:00:00"))
    print(loader.load_distribution_network(feeder="glover"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_l2"))
    print(simulator.set_cable_current_limits(rating_multiplier=1.08))
    print(simulator.set_voltage_limits(default_vmin_pu=0.96, default_vmax_pu=1.04, exception_bus_ids=None, exception_vmin_pu=None, exception_vmax_pu=None))
    print(simulator.build_objective(analysis_type="dhc_l2"))
    print(simulator.solve())
    print(simulator.update_network_voltages())
    print(analyzer.export_data_to_file(export_type="voltages", file_format="json"))


if __name__ == "__main__":
    main()

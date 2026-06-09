from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-20 12:00:00"))
    print(loader.load_solar(feeder="glover", timestamp="2025-03-20 12:00:00"))
    print(loader.load_distribution_network(feeder="glover"))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="infeasibility_l1"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.96, default_vmax_pu=1.04))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.08))
    print(simulator.build_objective(analysis_type="infeasibility_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-5, max_iter=400))
    print(simulator.update_bus_infeasible_currents(analysis_type="infeasibility_l1"))
    print(simulator.update_network_voltages())
    print(analyzer.list_top_buses(metric="infeasibility", top_k=5))
    print(analyzer.export_data_to_file(export_type="voltages", file_format="json"))
    print(analyzer.plot_network_data(plot_type="infeasibility", feeder="glover"))


if __name__ == "__main__":
    main()

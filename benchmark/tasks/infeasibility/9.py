from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="south_hero", timestamp="2025-03-19 14:00:00"))
    print(loader.load_solar(feeder="south_hero", timestamp="2025-03-19 14:00:00"))
    print(loader.load_distribution_network(feeder="south_hero"))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="infeasibility_l2"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05, exception_bus_ids=["5", "12", "20"], exception_vmin_pu=0.98, exception_vmax_pu=1.02))
    print(simulator.build_objective(analysis_type="infeasibility_l2"))
    print(simulator.solve(solver="ipopt", tolerance=1e-6, max_iter=400))
    print(simulator.update_bus_infeasible_currents(analysis_type="infeasibility_l2"))
    print(simulator.update_network_voltages())
    print(analyzer.plot_network_data(plot_type="voltage", feeder="south_hero"))
    print(analyzer.plot_network_data(plot_type="infeasibility", feeder="south_hero"))
    print(analyzer.list_top_buses(metric="infeasibility", top_k=5))


if __name__ == "__main__":
    main()

# WF8: L2 Infeasibility + Dual Plots (covers Q19, Q25, Q30)
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="rochester", timestamp="2025-03-18 18:00:00"))
    print(loader.load_solar(feeder="rochester", timestamp="2025-03-18 18:00:00"))
    print(loader.load_distribution_network(feeder="rochester"))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="infeasibility_l2"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.94, default_vmax_pu=1.06,
          exception_bus_ids=None, exception_vmin_pu=None, exception_vmax_pu=None))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.10))
    print(simulator.build_objective(analysis_type="infeasibility_l2"))
    print(simulator.solve(solver="ipopt", tolerance=1e-6, max_iter=300))
    print(simulator.update_bus_infeasible_currents(
        analysis_type="infeasibility_l2"))
    print(simulator.update_network_voltages())
    print(analyzer.plot_network_data(
        plot_type="infeasibility", feeder="rochester"))
    print(analyzer.plot_network_data(plot_type="voltage", feeder="rochester"))
    print(analyzer.list_top_buses(metric="infeasibility", top_k=3))


if __name__ == "__main__":
    main()

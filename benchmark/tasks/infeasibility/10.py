# WF9: L1 Infeasibility + Exception Bus Bounds (covers Q18, Q20, Q25, Q26, Q30)
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-23 10:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-23 10:00:00"))
    print(loader.load_distribution_network(feeder="stowe"))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="infeasibility_l1"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05,
          exception_bus_ids=["10", "25", "36"], exception_vmin_pu=0.985, exception_vmax_pu=1.015))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.15))
    print(simulator.build_objective(analysis_type="infeasibility_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-6, max_iter=500))
    print(simulator.update_bus_infeasible_currents(
        analysis_type="infeasibility_l1"))
    print(simulator.update_network_voltages())
    print(analyzer.export_data_to_file(
        export_type="voltages", file_format="csv"))
    print(analyzer.plot_network_data(plot_type="voltage", feeder="stowe"))


if __name__ == "__main__":
    main()

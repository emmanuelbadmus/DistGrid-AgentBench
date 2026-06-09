from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-23 10:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-23 10:00:00"))    
    print(loader.load_distribution_network(feeder="stowe"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="infeasibility_l2"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.94, default_vmax_pu=1.06, exception_bus_ids=["10", "25", "36"], exception_vmin_pu=0.98, exception_vmax_pu=1.02))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.15))
    print(simulator.build_objective(analysis_type="infeasibility_l2"))
    print(simulator.solve(solver="ipopt", tolerance=1e-6, max_iter=1000))
    print(simulator.update_bus_infeasible_currents(analysis_type="infeasibility_l2"))
    print(simulator.update_network_voltages())
    print(analyzer.plot_network_data(plot_type="infeasibility", feeder="stowe"))
    print(analyzer.plot_network_data(plot_type="voltage", feeder="stowe"))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="south_hero", timestamp="2025-03-22 18:00:00"))
    print(loader.load_solar(feeder="south_hero", timestamp="2025-03-22 18:00:00"))
    print(loader.load_distribution_network(feeder="south_hero"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_l1"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.95, default_vmax_pu=1.05, exception_bus_ids=None, exception_vmin_pu=None, exception_vmax_pu=None))
    print(simulator.build_objective(analysis_type="dhc_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-5, max_iter=500))
    print(simulator.update_loads_curtailed_power(analysis_type="dhc_l1"))
    print(analyzer.plot_network_data(plot_type="curtailment", feeder="south_hero"))
    print(analyzer.list_top_buses(metric="curtailment", top_k=3))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-17 14:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-17 14:00:00"))
    print(loader.load_distribution_network(feeder="stowe"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_l2"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.96, default_vmax_pu=1.04, exception_bus_ids=["2", "20"], exception_vmin_pu=0.98, exception_vmax_pu=1.02))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.10))
    print(simulator.build_objective(analysis_type="dhc_l2"))
    print(simulator.solve(solver="ipopt", tolerance=1e-6, max_iter=500))
    print(simulator.update_loads_curtailed_power(analysis_type="dhc_l2"))
    print(analyzer.list_top_buses(metric="curtailment", top_k=6))
    print(simulator.update_network_voltages())
    print(analyzer.plot_network_data(plot_type="voltage", feeder="stowe"))


if __name__ == "__main__":
    main()

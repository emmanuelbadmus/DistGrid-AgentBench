from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-18 21:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-18 21:00:00"))
    print(loader.load_distribution_network(feeder="stowe"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_l1"))
    print(simulator.set_voltage_limits(default_vmin_pu=0.94, default_vmax_pu=1.06, exception_bus_ids=["5", "15", "30"], exception_vmin_pu=0.97, exception_vmax_pu=1.03))
    print(simulator.build_objective(analysis_type="dhc_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-5, max_iter=200))
    print(simulator.update_loads_curtailed_power(analysis_type="dhc_l1"))
    print(analyzer.plot_network_data(plot_type="curtailment", feeder="stowe"))


if __name__ == "__main__":
    main()

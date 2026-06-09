from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-20 15:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-20 15:00:00"))
    print(loader.load_distribution_network(feeder="stowe"))

    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="dhc_l1"))
    print(simulator.build_objective(analysis_type="dhc_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4))
    print(simulator.update_loads_curtailed_power(analysis_type="dhc_l1"))
    print(analyzer.plot_network_data(plot_type="curtailment", feeder="stowe"))
    print(analyzer.list_top_buses(metric="curtailment", top_k=7))


if __name__ == "__main__":
    main()

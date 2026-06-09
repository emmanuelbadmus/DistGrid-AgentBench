from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-21 09:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-21 09:00:00"))
    print(loader.load_distribution_network(feeder="stowe"))
    print(simulator.create_and_initialize_model())
    print(simulator.set_voltage_limits(default_vmin_pu=0.96, default_vmax_pu=1.04))
    print(simulator.build_constraints(analysis_type="powerflow"))
    print(simulator.build_objective(analysis_type="powerflow"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=200))
    print(simulator.update_network_voltages())
    print(analyzer.export_data_to_file(export_type="voltages", file_format="csv"))


if __name__ == "__main__":
    main()

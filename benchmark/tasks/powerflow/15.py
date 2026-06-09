# WF10: Power Flow + JSON Export + Violation Check (covers Q12-14)
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="south_hero", timestamp="2025-03-17 19:00:00"))
    print(loader.load_solar(feeder="south_hero", timestamp="2025-03-17 19:00:00"))
    print(loader.load_distribution_network(feeder="south_hero"))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="powerflow"))
    print(simulator.build_objective(analysis_type="powerflow"))
    print(simulator.solve(solver="ipopt", tolerance=1e-5, max_iter=200))
    print(simulator.update_network_voltages())
    print(analyzer.export_data_to_file(
        export_type="voltages", file_format="json"))
    print(analyzer.check_voltage_violations())
    print(analyzer.get_bus_voltages(limit=20))


if __name__ == "__main__":
    main()

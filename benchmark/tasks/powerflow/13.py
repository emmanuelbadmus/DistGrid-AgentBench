# WF3: Power Flow + Violation Check + Plot (covers Q12-14, Q28)
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_load(feeder="rochester", timestamp="2025-03-19 22:00:00"))
    print(loader.load_solar(feeder="rochester", timestamp="2025-03-19 22:00:00"))
    print(loader.load_distribution_network(feeder="rochester"))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="powerflow"))
    print(simulator.build_objective(analysis_type="powerflow"))
    print(simulator.solve(solver="ipopt", tolerance=1e-4, max_iter=100))
    print(simulator.update_network_voltages())
    print(analyzer.check_voltage_violations())
    print(analyzer.plot_network_data(plot_type="voltage", feeder="rochester"))


if __name__ == "__main__":
    main()

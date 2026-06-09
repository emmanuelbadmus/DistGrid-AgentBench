from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-20 09:00:00"))
    print(loader.load_solar(feeder="glover", timestamp="2025-03-20 09:00:00"))
    print(loader.load_distribution_network(feeder="glover"))
    print(simulator.create_and_initialize_model())
    print(simulator.build_constraints(analysis_type="infeasibility_l1"))
    print(simulator.set_cable_current_limits(rating_multiplier=1.12))
    print(simulator.set_transformer_loading_limits(rating_multiplier=1.08))
    print(simulator.build_objective(analysis_type="infeasibility_l1"))
    print(simulator.solve(solver="ipopt", tolerance=1e-5, max_iter=600))
    print(simulator.update_bus_infeasible_currents(analysis_type="infeasibility_l1"))
    print(analyzer.list_top_buses(metric="infeasibility", top_k=3))
    print(simulator.update_network_voltages())
    print(analyzer.export_data_to_file(export_type="voltages", file_format="json"))


if __name__ == "__main__":
    main()

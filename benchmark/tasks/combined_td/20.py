from distgrid_bench.tools.combined_td import CombinedTDTools
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    combined = CombinedTDTools(registry)
    loader = NetworkLoader(registry)

    print(combined.load_transmission_network())
    print(loader.load_distribution_network(feeder='rochester'))
    print(combined.prepare_distribution_for_coupling(feeder='rochester'))
    print(combined.create_combined_td_model(transmission_poi_bus=14))
    print(combined.scale_combined_td_loads(system='transmission', multiplier=1.15))
    print(combined.scale_combined_td_loads(system='distribution', multiplier=1.35))
    print(combined.run_combined_td_powerflow(solver='ipopt', tolerance=1e-06, max_iter=1000))
    print(combined.summarize_combined_td_results())
    print(combined.summarize_coupling_port())
    print(combined.list_combined_td_voltage_violations(top_k=10))
    print(combined.list_combined_td_weak_locations(top_k=10))
    print(combined.export_combined_td_results(export_type='summary', file_format='csv'))


if __name__ == "__main__":
    main()

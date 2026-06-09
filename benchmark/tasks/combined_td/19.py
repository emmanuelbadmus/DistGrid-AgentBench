from distgrid_bench.tools.combined_td import CombinedTDTools
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    combined = CombinedTDTools(registry)
    loader = NetworkLoader(registry)

    print(combined.load_transmission_network())
    print(loader.load_distribution_network(feeder='stowe'))
    print(combined.prepare_distribution_for_coupling(feeder='stowe'))
    print(combined.create_combined_td_model(transmission_poi_bus=14))
    print(combined.run_combined_td_powerflow(solver='ipopt', tolerance=1e-06, max_iter=1000))
    print(combined.summarize_combined_td_results())
    print(combined.summarize_coupling_port())
    print(combined.set_combined_td_voltage_limits(transmission_vmin_pu=0.98, transmission_vmax_pu=1.02, distribution_vmin_pu=0.96, distribution_vmax_pu=1.04))
    print(combined.list_combined_td_voltage_violations(top_k=10))
    print(combined.run_combined_td_infeasibility(norm='l2'))
    print(combined.list_combined_td_weak_locations(top_k=8))
    print(combined.export_combined_td_results(export_type='summary', file_format='json'))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.combined_td import CombinedTDTools
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry



def main():
    registry = SharedRegistry()
    combined = CombinedTDTools(registry)
    loader = NetworkLoader(registry)

    print(combined.load_transmission_network())
    print(loader.load_distribution_network(feeder="south_hero"))
    print(combined.prepare_distribution_for_coupling(feeder="south_hero"))
    print(combined.create_combined_td_model(transmission_poi_bus=14))
    print(combined.run_combined_td_powerflow(solver="ipopt", tolerance=1e-6, max_iter=1000))
    print(combined.list_combined_td_weak_locations(top_k=5))


if __name__ == "__main__":
    main()

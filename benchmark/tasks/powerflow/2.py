from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_simulator import NetworkSimulator


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    simulator = NetworkSimulator(registry)

    print(loader.load_distribution_network(feeder="glover"))
    print(simulator.create_and_initialize_model())


if __name__ == "__main__":
    main()

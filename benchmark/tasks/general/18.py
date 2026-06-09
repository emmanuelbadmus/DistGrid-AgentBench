from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer

def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="rochester", timestamp="2025-03-21 07:00:00"))
    print(loader.load_solar(feeder="rochester", timestamp="2025-03-21 07:00:00"))
    print(loader.load_distribution_network(feeder="rochester"))
    print(analyzer.calculate_total_power(power_type="load"))
    print(analyzer.calculate_total_power(power_type="solar"))
    print(analyzer.get_bus_voltages(limit=10))


if __name__ == "__main__":
    main()

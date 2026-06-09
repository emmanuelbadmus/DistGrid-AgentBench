from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="glover", timestamp="2025-03-22 18:00:00"))
    print(loader.load_distribution_network(feeder="glover"))
    print(analyzer.calculate_total_power(power_type="load"))
    print(analyzer.get_component_count(component_type="loads"))


if __name__ == "__main__":
    main()

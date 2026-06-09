# WF2: Load/Solar Totals + Net Demand (covers Q5-7 about power calculations)
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_load(feeder="stowe", timestamp="2025-03-20 15:00:00"))
    print(loader.load_solar(feeder="stowe", timestamp="2025-03-20 15:00:00"))
    print(loader.load_distribution_network(feeder="stowe"))
    print(analyzer.calculate_total_power(power_type="load"))
    print(analyzer.calculate_total_power(power_type="solar"))


if __name__ == "__main__":
    main()

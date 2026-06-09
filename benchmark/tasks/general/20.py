from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.combined_td import CombinedTDTools


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    combined = CombinedTDTools(registry)

    print(loader.load_load(feeder='rochester', timestamp='2025-03-20 02:00:00'))
    print(loader.load_solar(feeder='rochester', timestamp='2025-03-20 02:00:00'))
    print(loader.load_distribution_network(feeder='rochester'))
    print(analyzer.calculate_total_power(power_type='load'))
    print(analyzer.calculate_total_power(power_type='solar'))
    print(analyzer.export_data_to_file(export_type='nodes', file_format='json'))
    print(analyzer.export_nodes_by_voltage_condition(voltage=120.0, condition='eq', file_format='txt'))


if __name__ == "__main__":
    main()

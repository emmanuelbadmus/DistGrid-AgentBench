from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.combined_td import CombinedTDTools


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    combined = CombinedTDTools(registry)

    print(combined.load_transmission_network())
    print(combined.summarize_transmission_network())
    print(loader.load_distribution_network(feeder='stowe'))
    print(analyzer.get_component_count(component_type='buses'))
    print(analyzer.get_component_count(component_type='transformers'))
    print(analyzer.get_component_count(component_type='regulators'))
    print(analyzer.export_nodes_by_voltage_condition(voltage=240.0, condition='lt', file_format='csv'))


if __name__ == "__main__":
    main()

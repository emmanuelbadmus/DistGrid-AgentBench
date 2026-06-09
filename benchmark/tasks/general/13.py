# WF1: Component Counting (covers Q1-4 easy queries about counting)
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_distribution_network(feeder="glover"))
    print(analyzer.get_component_count(component_type="buses"))
    print(analyzer.get_component_count(component_type="lines"))
    print(analyzer.get_component_count(component_type="transformers"))


if __name__ == "__main__":
    main()

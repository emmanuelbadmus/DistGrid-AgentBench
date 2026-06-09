from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)
    
    print(loader.load_distribution_network(feeder="rochester"))
    print(analyzer.get_component_count(component_type="capacitors"))



if __name__ == "__main__":
    main()

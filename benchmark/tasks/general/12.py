# WF4: Without running any analysis - plot input voltages + export (covers Q11, Q8, Q10)
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_distribution_network(feeder="glover"))

    print(analyzer.plot_network_data(plot_type="voltage", feeder="glover"))
    print(analyzer.export_data_to_file(export_type="nodes", file_format="txt"))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.network.network_analyzer import NetworkAnalyzer
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    loader = NetworkLoader(registry)
    analyzer = NetworkAnalyzer(registry)

    print(loader.load_ev_charger_data(feeder="stowe", demand_scale=1.35))
    print(analyzer.list_ev_charger_candidates(top_k=8, sort_by="priority"))
    print(analyzer.list_ev_charger_candidates(top_k=5, sort_by="demand"))


if __name__ == "__main__":
    main()

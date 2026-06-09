from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)

    print(loader.load_pv_dataset(dataset_name="bed"))
    print(analyzer.analyze_growth(freq="Y"))
    print(analyzer.analyze_growth(freq="M"))


if __name__ == "__main__":
    main()

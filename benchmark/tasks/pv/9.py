from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer, PVGeneration


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)
    pf = PVGeneration(registry)

    print(loader.load_pv_dataset(dataset_name="bed"))
    print(analyzer.analyze_growth(freq="Y"))
    print(analyzer.detect_outliers(metric="capacity", percentile=99.0))
    print(analyzer.count_pv_systems(scope="active_model"))


if __name__ == "__main__":
    main()

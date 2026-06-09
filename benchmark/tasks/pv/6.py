from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)

    print(loader.load_pv_dataset(dataset_name="bed", substation_id=29, feeder_id=3))
    print(analyzer.count_pv_systems(scope="active_model"))
    print(analyzer.compare_with_feeder(
        dataset_name="vec", substation_id="29", feeder_id="4"))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)

    print(loader.load_pv_dataset(dataset_name="vec"))
    print(analyzer.get_substation(source="metadata"))
    print(analyzer.get_feeder(source="metadata"))
    print(analyzer.compare_with_feeder(
        dataset_name="vec", substation_id="29", feeder_id="3"))
    print(analyzer.filter_pv_systems(key="system_type",
          value="Residential", operator="equals"))
    print(analyzer.count_pv_systems(scope="active_model"))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)

    print(loader.load_pv_dataset(dataset_name="vec"))
    print(analyzer.count_pv_systems(scope="active_model"))
    print(analyzer.detect_missing_values(columns=['capacity', 'install_date']))
    print(analyzer.audit_metadata_integrity(strict=True))


if __name__ == "__main__":
    main()

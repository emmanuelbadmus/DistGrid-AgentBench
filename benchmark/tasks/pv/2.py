from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)

    print(loader.load_pv_dataset(dataset_name="gmp"))
    print(analyzer.detect_outliers(metric='capacity', percentile=99.0))
    print(analyzer.audit_metadata_integrity(strict=True))


if __name__ == "__main__":
    main()

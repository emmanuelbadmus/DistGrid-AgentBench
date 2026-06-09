from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)

    print(loader.load_pv_dataset(dataset_name="gmp"))
    print(analyzer.filter_pv_systems(
        key="install_year", value="2020", operator="gt"))
    print(analyzer.count_pv_systems(scope="active_model"))
    print(analyzer.estimate_pv_parameters(solver='ipopt', verbose=True))


if __name__ == "__main__":
    main()

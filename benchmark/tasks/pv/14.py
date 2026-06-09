from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer, PVGeneration


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)
    pf = PVGeneration(registry)

    print(loader.load_pv_dataset(dataset_name="gmp"))
    print(analyzer.filter_pv_systems(key="install_year", value=2018, operator="gt"))
    print(analyzer.estimate_pv_parameters(solver="ipopt"))
    print(pf.set_calculation_method(method="capacity"))
    print(pf.initialize_pv_output_model())
    print(pf.calculate_pv_output(execution_mode="sequential"))
    print(pf.summarize_pv_generation(verbosity="high"))


if __name__ == "__main__":
    main()

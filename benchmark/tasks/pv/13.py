from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer, PVGeneration


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)
    pf = PVGeneration(registry)

    print(loader.load_pv_dataset(dataset_name="bed"))
    print(analyzer.filter_pv_systems(key="inverter_model",
          value="Unknown", operator="contains"))
    # Note: Logic usually implies we filter TO remove unknown, but tool filters to KEEP match.
    # Example flows often demo functionality. Let's assume we want to study the unknowns here, or simulate correcting them.
    print(analyzer.estimate_pv_parameters(solver="ipopt", verbose=True))
    # fallback since unknown inverter
    print(pf.set_calculation_method(method="capacity"))
    print(pf.initialize_pv_output_model())
    print(pf.calculate_pv_output(execution_mode="sequential"))


if __name__ == "__main__":
    main()

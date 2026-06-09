from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer, PVGeneration


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)
    pf = PVGeneration(registry)

    print(loader.load_pv_dataset(dataset_name="vec"))
    print(pf.set_calculation_method(
        method="diode", timestamp="2016-07-04T12:00:00"))
    print(analyzer.estimate_pv_parameters(solver="ipopt", verbose=True))
    print(analyzer.load_pv_weather_data(source="local"))
    print(analyzer.compute_poa_irradiance(start_date="2016-07-04", start_time="00:00:00", end_time="23:59:59"))
    print(pf.initialize_pv_output_model())
    print(pf.calculate_pv_output(execution_mode="sequential"))
    print(pf.summarize_pv_generation(verbosity="high"))


if __name__ == "__main__":
    main()

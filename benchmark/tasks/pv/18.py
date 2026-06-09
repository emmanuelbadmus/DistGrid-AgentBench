from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer, PVGeneration


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)
    pf = PVGeneration(registry)

    print(loader.load_pv_dataset(dataset_name="vec"))
    print(analyzer.load_pv_weather_data(start_date="2016-07-05", check_time=True))
    print(analyzer.compute_poa_irradiance(start_date="2016-07-05",
          start_time="09:00:00", end_time="17:00:00"))
    print(analyzer.estimate_pv_parameters(solver="ipopt"))
    print(pf.set_calculation_method(method="diode"))
    print(pf.initialize_pv_output_model())
    print(pf.calculate_pv_output(execution_mode="sequential"))
    print(pf.summarize_pv_generation(verbosity="high"))
    print(analyzer.compare_with_feeder(
          dataset_name="vec", substation_id="29", feeder_id="3"))


if __name__ == "__main__":
    main()

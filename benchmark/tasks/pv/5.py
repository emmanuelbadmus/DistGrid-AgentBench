from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)

    print(loader.load_pv_dataset(dataset_name="vec"))
    print(analyzer.filter_pv_systems(key="inverter_model",
          value="Enphase", operator="contains"))
    print(analyzer.load_pv_weather_data(source="local"))
    print(analyzer.compute_poa_irradiance(start_date="2016-07-01", end_date="2016-07-01"))


if __name__ == "__main__":
    main()

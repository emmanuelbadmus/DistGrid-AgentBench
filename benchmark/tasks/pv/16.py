from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVGeneration


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    pf = PVGeneration(registry)

    print(loader.load_pv_dataset(dataset_name="vec"))
    print(pf.load_pv_weather_data(source="local"))
    print(pf.set_calculation_method(
        method='capacity', timestamp="2025-06-21T12:00:00"))
    print(pf.compute_poa_irradiance())
    print(pf.initialize_pv_output_model())
    print(pf.calculate_pv_output(execution_mode="sequential"))
    print(pf.summarize_pv_generation(verbosity="high"))
    print(pf.apply_capacity_scaling(factor=1.20))
    print(pf.calculate_pv_output(execution_mode="sequential"))
    print(pf.summarize_pv_generation(verbosity="high"))


if __name__ == "__main__":
    main()

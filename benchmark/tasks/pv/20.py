from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.pv_analysis import PVLoader, PVAnalyzer, PVGeneration


def main():
    registry = SharedRegistry()
    loader = PVLoader(registry)
    analyzer = PVAnalyzer(registry)
    pf = PVGeneration(registry)

    print(loader.load_pv_dataset(dataset_name='gmp'))
    print(analyzer.filter_pv_systems(key='install_date', value='2018-12-31', operator='gt'))
    print(analyzer.count_pv_systems())
    print(analyzer.analyze_market_share())
    print(analyzer.audit_metadata_integrity())
    print(pf.set_calculation_method(method='capacity', timestamp='2016-07-05 13:00:00'))
    print(pf.initialize_pv_output_model())
    print(pf.calculate_pv_output(execution_mode='sequential'))
    print(pf.summarize_pv_generation(verbosity='low'))
    print(analyzer.load_pv_weather_data(start_date='2016-07-05'))
    print(analyzer.compute_poa_irradiance(start_date='2016-07-05', start_time='09:00:00', end_time='17:00:00'))
    print(analyzer.estimate_pv_parameters(solver='ipopt', verbose=True))
    print(pf.set_calculation_method(method='diode', timestamp='2016-07-05 13:00:00'))
    print(pf.initialize_pv_output_model())
    print(pf.calculate_pv_output(execution_mode='sequential'))
    print(pf.summarize_pv_generation(verbosity='high'))
    print(analyzer.analyze_distribution(metric='capacity', bins=20))


if __name__ == "__main__":
    main()

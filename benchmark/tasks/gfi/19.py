from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.gfi_analysis import GFILoader, GFISimulator, GFIAnalyzer, GFIPlotter


def main():
    registry = SharedRegistry()
    loader = GFILoader(registry)
    simulator = GFISimulator(registry)
    analyzer = GFIAnalyzer(registry)
    plotter = GFIPlotter(registry)

    print(loader.load_gfi_parameters())
    print(simulator.set_gfi_mode(mode='FS', K_droop_f=35.0, f_db=0.0005))
    print(simulator.set_gfi_parameter(key='Pref_const', value=0.75))
    print(simulator.set_gfi_disturbance(phase_jump_angle=0.35, phase_jump_time=0.25))
    print(simulator.set_simulation_timespan())
    print(simulator.run_gfi_simulation(method='full'))
    print(analyzer.get_gfi_overshoot(variable='P_expr'))
    print(analyzer.get_gfi_overshoot(variable='Q_expr'))
    print(analyzer.get_gfi_settling_time())
    print(simulator.run_gfi_simulation(method='schur'))
    print(analyzer.compare_gfi_solvers())
    print(analyzer.check_gfi_stability())
    print(plotter.plot_gfi_results())


if __name__ == "__main__":
    main()

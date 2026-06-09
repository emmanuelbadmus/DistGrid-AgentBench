from distgrid_bench.tools.shared_registry import SharedRegistry
from distgrid_bench.tools.gfi_analysis import GFILoader, GFISimulator, GFIAnalyzer, GFIPlotter


def main():
    registry = SharedRegistry()
    loader = GFILoader(registry)
    simulator = GFISimulator(registry)
    analyzer = GFIAnalyzer(registry)
    plotter = GFIPlotter(registry)

    print(loader.load_gfi_parameters())
    print(simulator.set_gfi_mode(mode='VOLT-VAR', K_droop_v=25.0, Vdb=0.015))
    print(simulator.set_gfi_parameter(key='R_line_pu', value=3.5))
    print(simulator.set_gfi_parameter(key='X_line_pu', value=3.5))
    print(simulator.set_gfi_parameter(key='Tf_ig', value=0.001))
    print(simulator.set_gfi_disturbance(phase_jump_angle=0.25, Vmag_dist=0.88, phase_jump_time=0.2))
    print(simulator.set_simulation_timespan())
    print(simulator.run_gfi_simulation(method='full'))
    print(analyzer.check_gfi_stability())
    print(analyzer.get_gfi_overshoot(variable='Q_expr'))
    print(analyzer.get_gfi_settling_time())
    print(simulator.run_gfi_simulation(method='schur'))
    print(analyzer.compare_gfi_solvers())
    print(plotter.plot_gfi_results())


if __name__ == "__main__":
    main()

from distgrid_bench.tools.gfi_analysis import SharedRegistry, GFILoader, GFISimulator, GFIAnalyzer, GFIPlotter


def main():
    registry = SharedRegistry()
    loader = GFILoader(registry)
    simulator = GFISimulator(registry)
    analyzer = GFIAnalyzer(registry)
    plotter = GFIPlotter(registry)

    print(loader.load_gfi_parameters())
    print(simulator.set_gfi_mode(mode="VOLT-VAR", K_droop_v=15.0, Vdb=0.03))
    print(simulator.set_gfi_disturbance(Vmag_dist=0.92))
    print(simulator.set_simulation_timespan())
    print(simulator.run_gfi_simulation(method="full"))
    print(analyzer.check_gfi_stability())
    print(analyzer.get_gfi_settling_time())
    print(analyzer.get_gfi_overshoot(variable="Q_expr"))
    print(plotter.plot_gfi_results())


if __name__ == "__main__":
    main()

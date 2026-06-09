from distgrid_bench.tools.gfi_analysis import SharedRegistry, GFILoader, GFISimulator, GFIAnalyzer, GFIPlotter


def main():
    registry = SharedRegistry()
    loader = GFILoader(registry)
    simulator = GFISimulator(registry)
    analyzer = GFIAnalyzer(registry)
    plotter = GFIPlotter(registry)

    print(loader.load_gfi_parameters())
    print(simulator.set_gfi_mode(mode="PQ"))
    print(simulator.set_gfi_parameter(key="Tf_ig", value=0.001))
    print(simulator.set_gfi_disturbance(phase_jump_angle=0.15))
    print(simulator.set_simulation_timespan())
    print(simulator.run_gfi_simulation(method="full"))
    print(analyzer.check_gfi_stability())
    print(analyzer.get_gfi_settling_time())
    print(analyzer.get_gfi_overshoot(variable="P_expr"))


if __name__ == "__main__":
    main()

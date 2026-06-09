from distgrid_bench.tools.gfi_analysis import SharedRegistry, GFILoader, GFISimulator, GFIAnalyzer, GFIPlotter

def main():
    registry = SharedRegistry()
    loader = GFILoader(registry)
    simulator = GFISimulator(registry)
    analyzer = GFIAnalyzer(registry)
    plotter = GFIPlotter(registry)

    print(loader.load_gfi_parameters())
    print(simulator.set_gfi_mode(mode="PQ"))
    
    p = registry.get("gfi:params")
    print(simulator.set_gfi_parameter(key="R_line_pu", value=0.1426))
    print(simulator.set_gfi_parameter(key="X_line_pu", value=0.140423))
    
    print(simulator.set_gfi_disturbance(phase_jump_angle=0.1))
    print(simulator.set_simulation_timespan())
    print(simulator.run_gfi_simulation(method="full"))
    
    print(analyzer.check_gfi_stability())
    print(analyzer.get_gfi_settling_time())
    print(plotter.plot_gfi_results())

if __name__ == "__main__":
    main()

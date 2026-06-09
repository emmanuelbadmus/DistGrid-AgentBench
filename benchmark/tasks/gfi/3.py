from distgrid_bench.tools.gfi_analysis import SharedRegistry, GFILoader, GFISimulator, GFIAnalyzer, GFIPlotter

def main():
    registry = SharedRegistry()
    loader = GFILoader(registry)
    simulator = GFISimulator(registry)
    analyzer = GFIAnalyzer(registry)
    plotter = GFIPlotter(registry)

    print(loader.load_gfi_parameters())
    print(simulator.set_gfi_mode(mode="FS", K_droop_f=40.0, f_db=0.0005))
    print(simulator.set_simulation_timespan())
    print(simulator.run_gfi_simulation(method="schur"))
    
    print(analyzer.check_gfi_stability())
    print(analyzer.get_gfi_overshoot(variable="P_expr"))
    print(plotter.plot_gfi_results())

if __name__ == "__main__":
    main()

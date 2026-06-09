from distgrid_bench.tools.gfi_analysis import SharedRegistry, GFILoader, GFISimulator


def main():
    registry = SharedRegistry()
    loader = GFILoader(registry)
    simulator = GFISimulator(registry)

    print(loader.load_gfi_parameters())
    print(simulator.set_gfi_mode(mode="FS", K_droop_f=20.0, f_db=0.001))


if __name__ == "__main__":
    main()

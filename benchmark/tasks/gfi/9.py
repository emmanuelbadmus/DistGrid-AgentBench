from distgrid_bench.tools.gfi_analysis import SharedRegistry, GFILoader, GFISimulator


def main():
    registry = SharedRegistry()
    loader = GFILoader(registry)
    simulator = GFISimulator(registry)

    print(loader.load_gfi_parameters())
    print(simulator.set_gfi_mode(mode="VOLT-VAR", K_droop_v=20.0, Vdb=0.02))
    print(simulator.set_gfi_parameter(key="V_target", value=1.0))


if __name__ == "__main__":
    main()

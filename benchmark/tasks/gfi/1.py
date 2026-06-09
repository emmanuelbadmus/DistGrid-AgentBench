from distgrid_bench.tools.gfi_analysis import SharedRegistry, GFILoader, GFISimulator


def main():
    registry = SharedRegistry()
    loader = GFILoader(registry)
    simulator = GFISimulator(registry)

    print(loader.load_gfi_parameters())
    print(simulator.set_gfi_mode(mode="PQ"))
    print(simulator.set_gfi_parameter(key="Pref_const", value=0.85))
    print(simulator.set_gfi_parameter(key="Qref_const", value=0.05))


if __name__ == "__main__":
    main()

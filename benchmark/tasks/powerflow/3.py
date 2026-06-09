from distgrid_bench.tools.combined_td import CombinedTDTools
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    transmission = CombinedTDTools(registry)

    print(transmission.load_transmission_network())
    print(transmission.list_transmission_voltage_violations(vmin_pu=0.95, vmax_pu=1.05))


if __name__ == "__main__":
    main()

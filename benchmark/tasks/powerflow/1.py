from distgrid_bench.tools.combined_td import CombinedTDTools
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    transmission = CombinedTDTools(registry)

    print(transmission.load_transmission_network())
    print(transmission.get_transmission_bus_voltage(bus_id=14))


if __name__ == "__main__":
    main()

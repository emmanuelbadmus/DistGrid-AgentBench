from distgrid_bench.tools.combined_td import CombinedTDTools
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    transmission = CombinedTDTools(registry)

    print(transmission.load_transmission_network())
    print(transmission.summarize_transmission_network())


if __name__ == "__main__":
    main()

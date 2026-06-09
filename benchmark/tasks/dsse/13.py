from distgrid_bench.tools.dsse_adapter import DSSEAdapter
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    dsse = DSSEAdapter(registry)
    loader = NetworkLoader(registry)

    print(loader.load_distribution_network(feeder="stowe"))
    print(dsse.load_dsse_case(feeder="stowe"))
    print(dsse.run_truth_powerflow())
    print(dsse.generate_measurements_from_truth(noise_std_pu=0.002, coverage=0.9))
    print(dsse.inject_bad_data(target_fraction=0.08, magnitude_pu=-0.05))
    print(dsse.build_measurement_topology())
    print(dsse.run_dsse())
    print(dsse.detect_bad_data(normalized_residual_threshold=2.5))


if __name__ == "__main__":
    main()

from distgrid_bench.tools.dsse_adapter import DSSEAdapter
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    dsse = DSSEAdapter(registry)
    loader = NetworkLoader(registry)

    print(loader.load_distribution_network(feeder="rochester"))
    print(dsse.load_dsse_case(feeder="rochester"))
    print(dsse.run_truth_powerflow())
    print(dsse.generate_measurements_from_truth(noise_std_pu=0.004, coverage=0.85))
    print(dsse.drop_measurements(drop_fraction=0.25))
    print(dsse.build_measurement_topology())
    print(dsse.run_dsse(use_pseudo_measurements=True))
    print(dsse.compute_state_estimation_error())


if __name__ == "__main__":
    main()

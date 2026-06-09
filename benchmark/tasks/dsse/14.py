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
    print(dsse.generate_measurements_from_truth(noise_std_pu=0.01, coverage=0.8))
    print(dsse.build_measurement_topology())
    print(dsse.run_dsse(use_pseudo_measurements=True))
    print(dsse.compute_state_estimation_error())
    print(dsse.export_dsse_report(file_format="txt"))
    print(dsse.plot_residuals())


if __name__ == "__main__":
    main()

from distgrid_bench.tools.dsse_adapter import DSSEAdapter
from distgrid_bench.tools.network.network_loader import NetworkLoader
from distgrid_bench.tools.shared_registry import SharedRegistry


def main():
    registry = SharedRegistry()
    dsse = DSSEAdapter(registry)
    loader = NetworkLoader(registry)

    print(loader.load_distribution_network(feeder="glover"))
    print(dsse.load_dsse_case(feeder="glover"))
    print(dsse.run_truth_powerflow())
    print(dsse.generate_measurements_from_truth(noise_std_pu=0.005, coverage=0.65))
    print(dsse.drop_measurements(drop_fraction=0.4))
    print(dsse.build_measurement_topology())
    print(dsse.run_dsse(use_pseudo_measurements=False))
    print(dsse.export_dsse_report(file_format="csv"))


if __name__ == "__main__":
    main()

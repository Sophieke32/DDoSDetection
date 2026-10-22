from mininet.log import setLogLevel
from experiments.test_topologies import test_topologies
from lib.network import Network
from lib.traffic_generator.dumb_attack import perform_dumb_attack
import random

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    # network = Network(get_single_switch_topology(2))
    # network = Network(pcap_to_network("../resources/pcaps/combined_Mirai_and_Benign_dataset_Full.csv"))
    # network = Network(test_topologies.get_tree_topology(
    #     [
    #         lambda : random.randint(2, 3),  # Core switch has 2-3 connections
    #         lambda : random.randint(1, 2),  # First layer switches have 1-2 connections
    #         lambda : 3                            # 3 stations at the leaves of the network
    #     ],
    #     lambda : random.randint(1, 2),  # Somewhere between 1 and 2 malicious nodes
    #     lambda : random.randint(2, 3),  # Somewhere between 2 and 3 benign nodes
    # ))

    network = Network(test_topologies.get_distributed_topology(
        [               # 1 central checker
            lambda: 4,            # 4 checkers below the central checker
            lambda: 2,            # which in turn each have 2 checkers below them
            lambda: 2,            # which in turn each have 2 checkers below them
            lambda: 3             # which in turn each have 2 endpoints below them
        ],
        lambda : random.randint(3, 5),  # Somewhere between 3 and 5 malicious nodes
        lambda : random.randint(2, 4),  # Somewhere between 2 and 4 benign nodes
    ))

    network.topology.visualise()

    network.start_net()

    perform_dumb_attack(network)

    network.stop_net()

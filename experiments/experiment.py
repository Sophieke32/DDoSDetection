from mininet.log import setLogLevel
from experiments.test_topologies import test_topologies
from lib.network import Network
import random

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    # network = Network(get_single_switch_topology(2))
    # network = Network(pcap_to_network("../resources/pcaps/combined_Mirai_and_Benign_dataset_Full.csv"))
    network = Network(test_topologies.get_tree_topology(
        [
            lambda : random.randint(3, 6),  # Core switch has 5-8 connections
            lambda : random.randint(2, 3),  # First layer switches have 2-3 connections
            lambda : 3                            # 3 stations at the leaves of the network
        ],
        lambda : random.randint(5, 8),  # Somewhere between 5 and 8 malicious nodes
        lambda : random.randint(2, 3),  # Somewhere between 2 and 3 benign nodes
    ))

    network.topology.visualise()

    network.start_net()
from mininet.log import setLogLevel
from lib.network import Network
from test_topologies import *
from lib.pcap_interpreter.pcap_interpreter import pcap_to_network

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    # network = Network(get_single_switch_topology(2))
    network = Network(pcap_to_network("resources/pcaps/combined_Mirai_and_Benign_dataset_Full.csv"))

    network.start_net()
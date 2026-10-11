from mininet.log import setLogLevel
from lib.network import Network
from test_topologies import *

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')
    network = Network(get_single_switch_topology(2))

    network.start_net()
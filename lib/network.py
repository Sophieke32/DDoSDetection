from lib.topologies.topology import Topology
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import info
from subprocess import Popen

class Network:
    topology = None

    def __init__(self, topology: Topology):
        self.tmp = 'tmp.txt'
        self.data = {}
        self.controller_ip = '192.168.1.26'
        self.controller_port = 6633
        self.topology = topology

    # Clears everything going on the network
    def clear_net(self):
        info('### Clearing net... ###')
        cmd = "mn -c"
        Popen(cmd, shell=True).wait()


    def start_net(self):
        info('### Starting net... ###')
        self.topology.build()
        net = Mininet(self.topology, controller=None)
        net.start()

        info('Dumping host connections')
        dumpNodeConnections(net.hosts)

        info('### Network is built, testing connectivity... ###')
        net.pingAll()
        net.stop()



# Keep track of all nodes, access points, connections, etc.
# Way to start, way to shut down
# Should have a list of traffics (traffic is usually derived from a pcap. Can be malicious, doesn't have to be)
# Ideally has a way to visualise itself

# has a from_pcap() method to create it from a pcap
# has a from_topology() method that creates it from a topology



# PCAP -> Network + attack
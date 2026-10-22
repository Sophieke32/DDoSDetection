from mininet.node import OVSSwitch, RemoteController
from lib.topologies.topology import Topology
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import info
from mininet.cli import CLI
from subprocess import Popen

class Network:
    topology = None
    controller = None

    def __init__(self, topology: Topology):
        self.tmp = 'tmp.txt'
        self.data = {}
        self.controller_ip = '192.168.1.26'
        self.controller_port = 6633
        self.topology = topology
        self.controller = None
        self.net = None

    # Clears everything going on the network
    def clear_net(self):
        info('### Clearing net... ###')
        cmd = "mn -c"
        Popen(cmd, shell=True).wait()


    def start_net(self):
        info('\n### Network initialisation ###\n\n')
        self.topology.build()
        net = Mininet(
            self.topology,
            controller=RemoteController,
            switch=OVSSwitch,
            build=False
        )
        net.addController(
            'c0',
            controller=RemoteController,
            ip='127.0.0.1',
            port=6633
        )
        net.start()

        info('\n### Host connections ###\n')
        dumpNodeConnections(net.hosts)

        info('\n### Network is built, testing connectivity... ###\n')
        net.pingAll()
        # CLI(net)

    def stop_net(self):
        self.net.stop()
        self.clear_net()



# Keep track of all nodes, access points, connections, etc.
# Way to start, way to shut down
# Should have a list of traffics (traffic is usually derived from a pcap. Can be malicious, doesn't have to be)
# Ideally has a way to visualise itself

# has a from_pcap() method to create it from a pcap
# has a from_topology() method that creates it from a topology



# PCAP -> Network + attack
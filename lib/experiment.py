import datetime
import os
from subprocess import Popen

from mininet.cli import CLI
from mininet.log import info
from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.util import dumpNodeConnections

from lib.topologies.topology import Topology


class Experiment:
    topology: Topology
    net: Mininet
    internal_behaviour: None
    external_behaviour: None
    name: str

    def __init__(self, topology: Topology, internal_behaviour: None, external_behaviour: None, name):
        self.topology = topology
        self.internal_behaviour = internal_behaviour
        self.external_behaviour = external_behaviour
        self.name = name


    def start_net(self):
        info('\n### Network initialisation ###\n\n')

        # Clear anything left from Mininet from last time
        self.__clear_net__()

        self.topology.build_network()
        net = Mininet(
            self.topology,
            switch=OVSBridge,
            controller=None,
            build=False
        )
        self.net = net
        net.start()

        info('\n### Host connections ###\n')
        dumpNodeConnections(net.hosts)

        info('\n### Network is built, testing connectivity... ###\n')
        net.pingAll()
        CLI(self.net)

    def upload_internal_behaviour(self):
        # Upload the internal behaviour to the nodes?
        pass


    def start_traffic(self):
        # Upload the external behaviour and start running
        pass


    def stop_net(self):
        self.net.stop()
        self.__clear_net__()


    # Clears everything going on the network.
    # This is an internal method, please use stop_net instead.
    def __clear_net__(self):
        info('### Clearing net... ###')
        cmd = "mn -c"
        Popen(cmd, shell=True).wait()

    def create_summary(self):
        os.chdir("results")
        print(os.getcwd())
        self.topology.save_visualisation("topology_visualisation")
        with open(os.getcwd() + "/" + self.name + "_" + str(datetime.datetime.now()), "w") as f:
            f.write("Experiment: " + self.name + "\n")

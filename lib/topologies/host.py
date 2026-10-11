from lib.topologies.node import Node
from lib.topologies.topology import Topology


class Host(Node):
    def __init__(self, topology: Topology, name=None):
        super().__init__()
        self.topology = topology
        if name is None:
            name = self.generate_name()
        self.name = name


    def generate_name(self):
        return "host " + self.topology.counters["hosts"]

    def create(self):
        self.mn_representation = self.topology.addHost(self.name, protocols='OpenFlow13')

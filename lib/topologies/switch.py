from lib.topologies.node import Node
from lib.topologies.topology import Topology

class Switch(Node):
    def __init__(self, topology: Topology, name=None):
        super().__init__()
        self.topology = topology
        if name is None:
            name = self.generate_name()
        self.name = name

    def generate_name(self):
        return "switch " + self.topology.counters["switches"]

    def create(self):
        self.mn_representation = self.topology.addSwitch(self.name, protocols='OpenFlow13')


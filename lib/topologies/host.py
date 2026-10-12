from lib.topologies.node import Node
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topology import Topology

class Host(Node):
    def __init__(self, topology: Topology, name=None, ip=None):
        super().__init__()
        self.topology = topology
        self.topology.counters["hosts"] += 1

        if name is None:
            name = self.generate_name()
        self.name = name
        if ip is not None:
            self.ip = ip


    def generate_name(self):
        return "host" + str(self.topology.counters["hosts"])

    def build(self):
        self.mn_representation = self.topology.addHost(self.name, protocols='OpenFlow13')

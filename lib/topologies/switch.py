from lib.topologies.node import Node
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topology import Topology

class Switch(Node):
    topology = None
    name = None

    def __init__(self, topology: Topology, name=None, ip=None, colour='#000000'):
        super().__init__(colour=colour)
        self.topology = topology

        if name is None:
            name = self.generate_name()
        self.name = name

        if ip is not None:
            self.ip = ip

    def generate_name(self):
        return "s" + str(len(self.topology.switch_objects))

    def build(self):
        self.mn_representation = self.topology.addSwitch(self.name, protocols='OpenFlow13')


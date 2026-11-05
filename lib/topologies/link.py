from lib.topologies.node import Node
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topology import Topology

class Link:
    def __init__(self, topology: Topology, src: Node, dst: Node, connection=False):
        self.topology = topology

        self.src = src
        self.dst = dst
        self.name = src.name + "_" + dst.name
        self.mn_representation = None
        self.connection = connection
        if connection:
            self.colour = "#000000"
        else:
            self.colour = "#FF0000"

    def build(self):
        self.mn_representation = self.topology.addLink(self.src.mn_representation, self.dst.mn_representation, protocols='OpenFlow13')
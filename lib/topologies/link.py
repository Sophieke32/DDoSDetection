from mininet.topo import Topo
from lib.topologies.node import Node
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from many_endpoints_topology import ManyEndpointsTopology

class Link:
    def __init__(self, topology: Topo, src: Node, dst: Node):
        self.topology = topology

        self.src = src
        self.dst = dst
        self.name = src.name + "_" + dst.name
        self.mn_representation = None

    def build(self):
        self.mn_representation = self.topology.addLink(self.src.mn_representation, self.dst.mn_representation, protocols='OpenFlow13')
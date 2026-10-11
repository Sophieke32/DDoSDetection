from lib.topologies.node import Node

class Link:
    def __init__(self, topology, src: Node, dst: Node):
        self.topology = topology
        self.src = src
        self.dst = dst
        self.name = src.name + " - " + dst.name
        self.mn_representation = None

    def create(self):
        self.mn_representation = self.topology.addLink(self.name, self.src, self.dst, protocols='OpenFlow13')
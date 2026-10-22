from lib.topologies.host import Host
from lib.topologies.many_endpoints_topology import ManyEndpointsTopology
from lib.topologies.switch import Switch

class Checker(Host):
    children: list[Checker | Switch] = []
    topology: ManyEndpointsTopology

    def __init__(self, topology: ManyEndpointsTopology, name=None, ip=None, colour='#000000', children=None):
        if name is None:
            name = "c" + str(topology.number_of_checkers())
        super().__init__(topology, name=name, ip=ip, colour=colour)

        if children is not None:
                children = children

    def add_child(self, child):
        self.children.append(child)


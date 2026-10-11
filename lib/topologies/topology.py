from mininet.topo import Topo
from lib.topologies.node import Node
from lib.topologies.host import Host
from lib.topologies.link import Link
from lib.topologies.switch import Switch

class Topology(Topo):
    host_objects: list[Host] = []
    switch_objects: list[Switch] = []
    link_objects: list[Link] = []
    counters = {"hosts": 0, "switches": 0, "links": 0}

    def __init__(self, *args, **params):
        super().__init__(*args, **params)
        # self.host_objects: list[Host] = []
        # self.switch_objects: list[Switch] = []
        # self.link_objects: list[Link] = []
        # self.counters = {"hosts": 0, "switches": 0, "links": 0}

    def build(self):
        for i in self.__get_nodes__():
            i.build()

        for i in self.link_objects:
            i.build()


    def __get_nodes__(self) -> list[Node]:
        return self.switch_objects + self.host_objects

    def add_switch(self, switch):
        self.switch_objects.append(switch)

    def add_host(self, host):
        self.host_objects.append(host)

    def add_link(self, link):
        self.link_objects.append(link)

# Should define the entire network
# Try to figure out an easy way to create these?
# Store these networks in a database?
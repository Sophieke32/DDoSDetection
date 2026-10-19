from mininet.topo import Topo
from lib.topologies.node import Node
from lib.topologies.host import Host
from lib.topologies.link import Link
from lib.topologies.switch import Switch
from mininet.log import info
from lib.topologies.topology_visualisation import visualise_topology

class Topology(Topo):
    benign_hosts: list[Host] = []
    malicious_hosts: list[Host] = []
    internal_hosts: list[Host] = []
    switch_objects: list[Switch] = []
    link_objects: list[Link] = []

    def __init__(self, *args, **params):
        super().__init__(*args, **params)

    def build(self):
        info(f"### AAAA Building network with {len(self.get_host_objects()) + len(self.switch_objects)} nodes"
             f" and {len(self.link_objects)} links\n")

        for i in self.get_nodes():
            i.build()

        for i in self.link_objects:
            i.build()


    def get_nodes(self) -> list[Node]:
        return self.switch_objects + self.get_host_objects()

    def add_switch(self, switch):
        self.switch_objects.append(switch)
        return switch

    def add_benign_host(self, host):
        self.benign_hosts.append(host)
        return host

    def add_malicious_host(self, host):
        self.malicious_hosts.append(host)
        return host

    def add_internal_host(self, host):
        self.internal_hosts.append(host)
        return host

    def add_link(self, link):
        self.link_objects.append(link)
        return link

    def get_host_objects(self):
        return self.benign_hosts + self.malicious_hosts + self.internal_hosts

    def visualise(self):
        visualise_topology(self)

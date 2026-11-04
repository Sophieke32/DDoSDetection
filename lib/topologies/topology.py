from mininet.topo import Topo
from lib.topologies.node import Node
from lib.topologies.host import Host
from lib.topologies.link import Link
from lib.topologies.switch import Switch
from mininet.log import info
import networkx as nx
import matplotlib.pyplot as plt

class Topology(Topo):
    benign_hosts: list[Host] = []       # Holds all the external benign hosts
    malicious_hosts: list[Host] = []    # Holds all the external malicious hosts
    internal_hosts: list[Host] = []     # Holds all internal nodes in the network
    switch_objects: list[Switch] = []   # Holds all the switch objects in the network
    link_objects: list[Link] = []       # Holds all the link objects in the network

    def __init__(self, *args, **params):
        super().__init__(*args, **params)

    def build_network(self):
        info(f"### AAAA Building network with {len(self.get_all_hosts()) + len(self.switch_objects)} nodes"
             f" and {len(self.link_objects)} links\n")

        for i in self.get_all_nodes():
            i.build()

        for i in self.get_all_links():
            i.build()


    def add_benign_host(self, host):
        self.benign_hosts.append(host)
        return host

    def add_malicious_host(self, host):
        self.malicious_hosts.append(host)
        return host

    def add_internal_host(self, host):
        self.internal_hosts.append(host)
        return host

    def add_switch(self, switch):
        self.switch_objects.append(switch)
        return switch

    def add_link(self, link):
        self.link_objects.append(link)
        return link

    def remove_link(self, link):
        self.link_objects.remove(link)

    def remove_links_from_node(self, node):
        for link in self.link_objects:
            if link.dst == node or link.src == node:
                self.remove_link(link)

    def remove_switch(self, switch):
        self.switch_objects.remove(switch)
        self.remove_links_from_node(switch)

    def remove_host(self, host):
        if host in self.internal_hosts:
            self.internal_hosts.remove(host)
        if host in self.malicious_hosts:
            self.malicious_hosts.remove(host)
        if host in self.benign_hosts:
            self.benign_hosts.remove(host)
        self.remove_links_from_node(host)

    def get_external_nodes(self):
        return self.benign_hosts + self.malicious_hosts

    def get_all_hosts(self):
        return self.benign_hosts + self.malicious_hosts + self.internal_hosts

    def get_all_switches(self):
        return self.switch_objects

    def get_all_nodes(self) -> list[Node]:
        return self.switch_objects + self.get_all_hosts()

    def get_all_links(self):
        return self.link_objects

    """
    Creates a visualisation of the network using matplotlib. Useful for debugging. 
    """
    def visualise(self):
        g = nx.Graph()

        hosts = self.get_all_hosts()
        for node in hosts:
            g.add_node(node.name, colour=node.colour)

        switches = self.switch_objects
        for node in switches:
            g.add_node(node.name, colour=node.colour)

        for link in self.link_objects:
            g.add_edge(link.src.name, link.dst.name)

        colours = [g.nodes[n]["colour"] for n in g.nodes]

        nx.draw(g, with_labels=True, node_color=colours)
        plt.show()

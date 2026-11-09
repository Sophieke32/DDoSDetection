from mininet.topo import Topo

from lib.topologies.connection import Connection
from lib.topologies.network_error import TopologyError
from lib.topologies.node import Node
from lib.topologies.host import Host
from lib.topologies.link import Link
from lib.topologies.switch import Switch
from mininet.log import info
import networkx as nx
import matplotlib.pyplot as plt

class Topology(Topo):
    benign_external_hosts: list[Host] = []               # Holds all the external benign hosts
    malicious_external_hosts: list[Host] = []            # Holds all the external malicious hosts
    benign_internal_hosts: list[Host] = []      # Holds all benign internal nodes in the network
    malicious_internal_hosts: list[Host] = []   # Holds all malicious internal nodes in the network
    switch_objects: list[Switch] = []           # Holds all the switch objects in the network
    connections: list[Connection] = []          # Used to connect two nodes
    link_objects: list[Link] = []               # Holds all the link objects in the network

    def __init__(self, *args, **params):
        super().__init__(*args, **params)

    def build_network(self):
        info(f"### AAAA Building network with {len(self.get_all_hosts()) + len(self.switch_objects)} nodes"
             f" and {len(self.link_objects)} links\n")

        for i in self.get_all_nodes():
            i.build()

        for i in self.get_all_links():
            i.build()

    def add_external_host(self, host, benign=True):
        if benign:
            self.benign_external_hosts.append(host)
        else:
            self.malicious_external_hosts.append(host)
        return host

    def add_internal_host(self, host, benign=True):
        if benign:
            self.benign_internal_hosts.append(host)
        else:
            self.malicious_internal_hosts.append(host)
        return host

    def make_internal_host_benign(self, host):
        if host in self.malicious_internal_hosts:
            self.benign_internal_hosts.append(host)
            self.malicious_internal_hosts.remove(host)
        else:
            raise TopologyError("Tried to make non-malicious host benign: " + host)

    def make_internal_host_malicious(self, host):
        if host in self.benign_internal_hosts:
            self.malicious_internal_hosts.append(host)
            self.benign_internal_hosts.remove(host)
        else:
            raise TopologyError("Tried to make non-benign host malicious: " + host)

    def add_switch(self, switch):
        self.switch_objects.append(switch)
        return switch

    # Note: If you are trying to connect two hosts, use a Connection instead.
    def add_link(self, link):
        self.link_objects.append(link)
        return link

    def add_connection(self, connection):
        self.connections.append(connection)
        self.switch_objects.append(connection.get_switch())
        self.link_objects.append(connection.get_src_link())
        self.link_objects.append(connection.get_dst_link())
        return connection

    def remove_connection(self, connection):
        self.connections.remove(connection)
        self.link_objects.remove(connection.get_src_link())
        self.link_objects.remove(connection.get_dst_link())
        self.switch_objects.remove(connection.get_switch())

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
        if host in self.benign_internal_hosts:
            self.benign_internal_hosts.remove(host)
        if host in self.malicious_internal_hosts:
            self.malicious_internal_hosts.remove(host)
        if host in self.malicious_external_hosts:
            self.malicious_external_hosts.remove(host)
        if host in self.benign_external_hosts:
            self.benign_external_hosts.remove(host)
        self.remove_links_from_node(host)

    def get_external_nodes(self):
        return self.benign_external_hosts + self.malicious_external_hosts

    def get_internal_hosts(self):
        return self.benign_internal_hosts + self.malicious_internal_hosts

    def get_all_hosts(self):
        return self.benign_external_hosts + self.malicious_external_hosts + self.benign_internal_hosts + self.malicious_internal_hosts

    def get_all_switches(self):
        return self.switch_objects

    def get_all_nodes(self) -> list[Node]:
        return self.switch_objects + self.get_all_hosts()

    def get_all_links(self):
        return self.link_objects

    def get_all_connections(self):
        return self.connections

    """
    Creates a visualisation of the network using matplotlib. Useful for debugging. 
    """
    def create_visualisation(self):
        fig = plt.figure(figsize=(12, 12))
        ax = plt.subplot(111)
        ax.set_title('Topology', fontsize=10)

        g = nx.Graph()

        hosts = self.get_all_hosts()
        for node in hosts:
            g.add_node(node.name, colour=node.colour)

        switches = self.switch_objects
        for node in switches:
            g.add_node(node.name, colour=node.colour)

        for connection in self.get_all_connections():
            g.add_edge(connection.src.name, connection.dst.name, colour=connection.get_src_link().colour)

        for link in self.get_all_links():
            if not link.connection:
                g.add_edge(link.src.name, link.dst.name, colour=link.colour)


        node_colours = [g.nodes[n]["colour"] for n in g.nodes]
        edge_colours = [g.edges[e]["colour"] for e in g.edges]

        nx.draw(g, with_labels=True, node_color=node_colours, edge_color=edge_colours)

        return g

    """
    Shows the visualisation
    """
    def show_visualisation(self):
        self.create_visualisation()
        plt.show(block=False)

    """
    Saves the visualisation
    """
    def save_visualisation(self, filename):
        self.create_visualisation()
        plt.savefig(filename + ".png")

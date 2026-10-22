import networkx as nx
from typing import TYPE_CHECKING
from mininet.log import warn
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from topology import Topology
    from many_endpoints_topology import ManyEndpointsTopology

"""
Creates a visualisation of the network using matplotlib. Useful for debugging. 
"""
def visualise_topology(topology: Topology):
    g = nx.Graph()

    hosts = topology.get_host_objects()
    for node in hosts:
        g.add_node(node.name, colour=node.colour)

    switches = topology.switch_objects
    for node in switches:
        g.add_node(node.name, colour=node.colour)

    for link in topology.link_objects:
        g.add_edge(link.src.name, link.dst.name)

    colours = [g.nodes[n]["colour"] for n in g.nodes]

    nx.draw(g, with_labels=True, node_color=colours)
    plt.show()


def visualise_many_endpoints_topology(topology: ManyEndpointsTopology):
    g = nx.Graph()

    for endpoint in topology.endpoints:
        g.add_node(endpoint.name, colour=endpoint.colour, layer=1)

    for layer, checkers in enumerate(topology.checkers):
        for checker in checkers:
            g.add_node(checker.name, colour=checker.colour, layer=(len(topology.checkers) - layer) + 2)

    top_layer = len(topology.checkers) + 2
    g.add_node(topology.aggregator.name, colour=topology.aggregator.colour, layer=top_layer)

    for host in topology.malicious_hosts + topology.benign_hosts:
        g.add_node(host.name, colour=host.colour, layer=0)

    for link in topology.link_objects:
        g.add_edge(link.src.name, link.dst.name)

    s = [n for n, data in g.nodes(data=True) if "layer" not in data]
    if s:
        warn("!!! Something went wrong: a host or switch was not included in the ManyEndpointsTopology"
             " object, but was included in one of its switches !!!")

    pos = nx.multipartite_layout(g, subset_key="layer", align="horizontal")

    colours = [g.nodes[n]["colour"] for n in g.nodes]
    # nx.draw_networkx_labels(g, pos, font_size=22, font_color="whitesmoke")
    nx.draw(g, pos, with_labels=True, node_color=colours)
    plt.show()
import networkx as nx
from typing import TYPE_CHECKING
import matplotlib.pyplot as plt

if TYPE_CHECKING:
    from topology import Topology

"""
Creates a visualisation of the network using matplotlib. Useful for debugging. 
"""
def visualise_topology(topology: Topology):
    g = nx.Graph()

    for node in topology.get_host_objects():
        g.add_node(node.name, colour=node.colour)

    for node in topology.switch_objects:
        g.add_node(node.name, colour=node.colour)

    for link in topology.link_objects:
        g.add_edge(link.src.name, link.dst.name)

    colours = [g.nodes[n]["colour"] for n in g.nodes]

    nx.draw(g, with_labels=True, node_color=colours)
    plt.show()


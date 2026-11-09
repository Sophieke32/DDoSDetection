from mininet.log import warn, info
import networkx as nx
import matplotlib.pyplot as plt

from lib.topologies.host import Host
from lib.topologies.switch import Switch
from lib.topologies.topology import Topology

"""
Topology where the internal network has many endpoints. Consists of a number of benign and
malicious nodes, which are connected to all endpoints (Switches). These endpoints are connected
to the aggregator (a Host), and to a checker (a subtype of Host). The core checker is connected
to the aggregator too, and optionally, the network may use intermediary checkers to connect 
endpoints to the core checker.
"""
class ManyEndpointsTopology(Topology):
    endpoints: list[Switch] = []
    checkers: list[list[Host]] = []
    aggregator: None | Host = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def build_network(self):
        info(f"### AAAA Building network with {len(self.get_all_hosts()) + len(self.get_all_switches())} nodes"
             f" and {len(self.link_objects)} links\n")

        for i in self.endpoints:
            i.build()

        for i in self.get_all_checkers():
            i.build()

        print(self.aggregator)
        self.aggregator.build()

        for i in self.get_external_nodes():
            i.build()

        for i in self.link_objects:
            i.build()


    def add_aggregator(self, aggregator: Host):
        if self.aggregator is not None:
            info("### Replacing existing aggregator with a new one ###")
            self.remove_host(self.aggregator)
        self.aggregator = aggregator
        self.internal_hosts.append(aggregator)
        return aggregator

    def add_checker(self, checker, layer):
        if len(self.checkers) < layer + 1:
            self.checkers.append([])
        self.checkers[layer].append(checker)
        return self.add_internal_host(checker)

    def add_endpoint(self, endpoint):
        self.endpoints.append(endpoint)
        return self.add_internal_host(endpoint)

    def number_of_checkers(self):
        res = 0
        for i in self.checkers:
            res += len(i)
        return res

    def get_all_checkers(self):
        res = []
        for i in self.checkers:
            for j in i:
                res.append(j)
        return res

    def get_endpoints(self):
        return self.endpoints

    def get_aggregator(self):
        return self.aggregator

    """
    Visualises the network as a graph using networkx
    
    Connections turn into a single black connection between the src and dst
    Manually made links render as a red line, as a warning to the user not to connect two hosts using just a link.
    """
    def visualise(self):
        g = nx.Graph()

        for endpoint in self.get_endpoints():
            g.add_node(endpoint.name, colour=endpoint.colour, layer=1)

        for layer, checkers in enumerate(self.checkers):
            for checker in checkers:
                g.add_node(checker.name, colour=checker.colour, layer=(len(self.checkers) - layer) + 2)

        top_layer = len(self.get_all_checkers()) + 2
        g.add_node(self.get_aggregator().name, colour=self.get_aggregator().colour, layer=top_layer)

        for host in self.get_external_nodes():
            g.add_node(host.name, colour=host.colour, layer=0)

        for connection in self.get_all_connections():
            g.add_edge(connection.src.name, connection.dst.name, colour=connection.get_src_link().colour)

        for link in self.get_all_links():
            if not link.connection:
                g.add_edge(link.src.name, link.dst.name, colour=link.colour)


        # Checks if any nodes were created while making edges. If so, raises a warning and prints those nodes.
        # Context: If an edge is made connecting a node that networkx does not yet know of (because you haven't made
        # it before), it will simply create a new node with that identifier. This means it would not have a
        # 'layer' attribute, which will raise an error at render-time.
        s = [n for n, data in g.nodes(data=True) if "layer" not in data]
        if s:
            warn("!!! Something went wrong: a host or switch was not included in the ManyEndpointsTopology"
                 " object, but was included in one of its switches !!!")
            print("\nSuspect nodes:")
            for i in s:
                print(i.name)

        pos = nx.multipartite_layout(g, subset_key="layer", align="horizontal")

        node_colours = [g.nodes[n]["colour"] for n in g.nodes]
        edge_colours = [g.edges[e]["colour"] for e in g.edges]

        nx.draw(g, pos, with_labels=True, node_color=node_colours, edge_color=edge_colours)
        plt.show()

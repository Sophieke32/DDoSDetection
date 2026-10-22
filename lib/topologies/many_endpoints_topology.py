from mininet.topo import Topo
from lib.topologies.host import Host
from lib.topologies.switch import Switch
from lib.topologies.link import Link
from mininet.log import info
from lib.topologies.topology_visualisation import visualise_many_endpoints_topology


"""
Topology where the internal network has many endpoints. Consists of a number of benign and
malicious nodes, which are connected to all endpoints (Switches). These endpoints are connected
to the aggregator (a Host), and to a checker (a subtype of Host). The core checker is connected
to the aggregator too, and optionally, the network may use intermediary checkers to connect 
endpoints to the core checker.
"""
class ManyEndpointsTopology(Topo):
    endpoints: list[Switch] = []
    checkers: list[list[Host]] = []
    aggregator = None
    benign_hosts: list[Host] = []
    malicious_hosts: list[Host] = []
    link_objects: list[Link] = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def build_network(self):
        info(f"### AAAA Building network with {len(self.get_all_hosts()) + len(self.get_all_switches())} nodes"
             f" and {len(self.link_objects)} links\n")

        for i in self.endpoints:
            i.build()

        for i in self.get_checkers():
            i.build()

        print(self.aggregator)
        self.aggregator.build()

        for i in self.get_external_hosts():
            i.build()

        for i in self.link_objects:
            i.build()


    def add_aggregator(self, aggregator: Host):
        if self.aggregator is not None:
            info("### Replacing existing aggregator with a new one ###")
        self.aggregator = aggregator
        return aggregator

    def add_checker(self, checker, layer):
        if len(self.checkers) < layer + 1:
            self.checkers.append([])
        self.checkers[layer].append(checker)
        return checker

    def add_endpoint(self, endpoint):
        self.endpoints.append(endpoint)
        return endpoint

    def add_link(self, link):
        self.link_objects.append(link)
        return link

    def number_of_checkers(self):
        res = 0
        for i in self.checkers:
            res += len(i)
        return res

    def get_checkers(self):
        res = []
        for i in self.checkers:
            for j in i:
                res.append(j)
        return res

    def get_external_hosts(self):
        return self.benign_hosts + self.malicious_hosts

    def get_all_hosts(self):
        return self.get_checkers() + self.get_external_hosts() + [self.aggregator]

    def get_all_switches(self):
        return self.endpoints

    def add_malicious_host(self, host):
        self.malicious_hosts.append(host)
        return host

    def add_benign_host(self, host):
        self.benign_hosts.append(host)
        return host

    def visualise(self):
        visualise_many_endpoints_topology(self)
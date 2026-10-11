from lib.topologies.topology import Topology
from lib.topologies.switch import Switch
from lib.topologies.host import Host
from lib.topologies.link import Link


def get_single_switch_topology(n):
    """Single switch, n hosts"""
    topology = Topology()
    switch = Switch(topology)
    topology.add_switch(switch)

    for i in range(n):
        host = Host(topology)
        topology.add_host(host)

        link = Link(topology, switch, host)
        topology.add_link(link)

    return topology

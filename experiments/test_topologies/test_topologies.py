from lib.topologies.many_endpoints_topology import ManyEndpointsTopology
from lib.topologies.switch import Switch
from lib.topologies.host import Host
from lib.topologies.link import Link
from lib.topologies.checker import Checker
from lib.topologies.network_error import NetworkError
from mininet.log import warn


# def get_single_switch_topology(n):
#     """Single switch, n hosts"""
#     topology = Topology()
#     switch = topology.add_switch(Switch(topology))
#
#     for i in range(n):
#         host = topology.add_internal_host(Host(topology))
#         topology.add_link(Link(topology, switch, host))
#
#     return topology


"""
Helper function for get_tree_topology.
Assumes tree_shape is a list of lambdas returning a number.
 
Creates all the internal nodes of the internal network. Does so by recursively calling itself 
with the tail (all elements but the first) of tree_shape.

If tree_shape is an empty list, raises an error. 
If it is of length one, that means we have
reached the leaves of the network, and so hosts should be created.
"""
def create_internal_network(tree_shape, parent, topology):
    if len(tree_shape) == 0:
        raise NetworkError("Cannot make empty internal network component!")
    if len(tree_shape) == 1:
        create_hosts(tree_shape[0], parent, topology)
        return

    for i in range(tree_shape[0]()):
        switch = topology.add_switch(Switch(topology, colour='#27ADF5'))
        topology.add_link(Link(topology, switch, parent))
        create_internal_network(tree_shape[1:], switch, topology)

"""
Helper function that creates the leaves of the internal network. 
Assumes number_of_hosts is a lambda that returns a number. 
"""
def create_hosts(number_of_hosts, parent, topology):
    for i in range(number_of_hosts()):
        host = topology.add_internal_host(Host(topology, colour='#27ADF5'))
        topology.add_link(Link(topology, host, parent))


"""
Method that generates a network consisting of two parts and a firewall node.

On one side, there's the internal network. The internal network is a tree structure, defined
by tree_shape, which is a list. Each element of the list should be a function that returns
a number (this can return the same number always, or you can add randomisation). Each element
in this list represents a layer of of the internal network. 

For example, given an array [lambda: 10, lambda: randInt(3, 4), lambda: randInt(1, 2)] creates
a network with one Core switch (connected to the firewall), which has 10 connections to intermediary switches. Each intermediary
switch has 3 or 4 connections to another layer of intermediary switches, which in turn have 1 or 2
connections to a final host. 

On the other side of the network, we use malicious and benign. These again are expected to be
functions that return a number, and that number determines how many malicious and how many benign
external nodes there will be. These will all be directly connected to the firewall node.
"""
# def get_tree_topology(tree_shape: list, malicious, benign):
#     if len(tree_shape) == 0:
#         raise NetworkError("Cannot make empty internal network!")
#     topology = Topology()
#     core_switch = topology.add_switch(Switch(topology, colour="000000"))
#
#     number_of_internal_nodes = len(topology.internal_hosts)
#
#     # Create the internal network of the topology
#     create_internal_network(tree_shape, core_switch, topology)
#
#     if number_of_internal_nodes == len(topology.internal_hosts):
#         warn("!!! Creating topology without an internal network !!!")
#
#     # Create the external network of the topology
#     number_of_malicious_nodes = malicious()
#     number_of_benign_nodes = benign()
#
#     if number_of_malicious_nodes + number_of_benign_nodes == 0:
#         warn("!!! Creating topology without an external network !!!")
#
#     for i in range(number_of_malicious_nodes):
#         host = topology.add_malicious_host(Host(topology, "m" + str(i), colour='#F55B27'))
#         topology.add_link(Link(topology, host, core_switch))
#
#     for i in range(number_of_benign_nodes):
#         host = topology.add_benign_host(Host(topology, "b" + str(i), colour="#07D962"))
#         topology.add_link(Link(topology, host, core_switch))
#
#     return topology


def create_checkers(tree_shape: list, parent, topology, layer):
    if len(tree_shape) == 0:
        raise NetworkError("Cannot make empty internal network!")
    if len(tree_shape) == 1:
        create_endpoints(tree_shape[0], parent, topology)
        return

    temp = tree_shape[0]()
    for i in range(temp):
        checker = topology.add_checker(Checker(topology, colour="#FAC72F"), layer) # Internal checkers are yellow
        topology.add_link(Link(topology, checker, parent))
        create_checkers(tree_shape[1:], checker, topology, layer + 1)


def create_endpoints(number_of_switches, parent, topology):
    temp = number_of_switches()
    for i in range(temp):
        switch = topology.add_endpoint(Switch(topology, colour='#27ADF5')) # Endpoints are blue
        topology.add_link(Link(topology, switch, parent))
        topology.add_link(Link(topology, switch, topology.aggregator))


"""
Works similarly to get_tree_topology, with net_shape taking over from tree_shape. It again
takes lambdas which return a number, though with new meaning for the numbers:

Each element of net_shape is a number of checkers branching from the core checker. For example:
[
   lambda : 4
   lambda : 2
]
Returns a core checker, which has 4 intermediary checkers, each in turn having two end-points.
Each endpoint is connected to every malicious and every benign host. 

On top of that, the network has an aggregator, which is connected to each endpoint, and to
the core checker.
"""
def get_distributed_topology(net_shape: list, malicious, benign):
    if len(net_shape) == 0:
        raise NetworkError("Cannot make empty internal network!")

    topology = ManyEndpointsTopology()
    core_checker = topology.add_checker(Checker(topology, colour='#000000', name="cc0"), 0) # core checker is black
    aggregator = topology.add_aggregator(Host(topology, colour='#000fff', name="agg0")) # aggregator is grey
    topology.add_link(Link(topology, aggregator, core_checker))

    number_of_checkers = topology.number_of_checkers()

    # Create the internal network
    create_checkers(net_shape, core_checker, topology, 1)

    if number_of_checkers == topology.number_of_checkers():
        warn("!!! Creating topology without an internal network !!!")

    # Create the external network of the topology
    number_of_malicious_nodes = malicious()
    number_of_benign_nodes = benign()

    if number_of_malicious_nodes + number_of_benign_nodes == 0:
        warn("!!! Creating topology without an external network !!!")

    for i in range(number_of_malicious_nodes):
        host = topology.add_malicious_host(Host(topology, "m" + str(i), colour='#F55B27')) # Malicious is red
        for endpoint in topology.endpoints:
            topology.add_link(Link(topology, host, endpoint))

    for i in range(number_of_benign_nodes):
        host = topology.add_benign_host(Host(topology, "b" + str(i), colour="#07D962")) # Benign is green
        for endpoint in topology.endpoints:
            topology.add_link(Link(topology, host, endpoint))

    return topology

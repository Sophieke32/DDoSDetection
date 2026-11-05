from lib.topologies.connection import Connection
from lib.topologies.topology import Topology
from lib.topologies.many_endpoints_topology import ManyEndpointsTopology
from lib.topologies.switch import Switch
from lib.topologies.host import Host
from lib.topologies.link import Link
from lib.topologies.checker import Checker
from lib.topologies.network_error import NetworkError
from mininet.log import warn



def build_external_network(benign, malicious, topology, benign_colour, malicious_colour, endpoints):
    number_of_malicious_nodes = malicious()
    number_of_benign_nodes = benign()

    if number_of_malicious_nodes + number_of_benign_nodes == 0:
        warn("!!! Creating topology without an external network !!!")

    for i in range(number_of_malicious_nodes):
        host = topology.add_malicious_host(Host(topology, "m" + str(i), colour=malicious_colour))
        for endpoint in endpoints:
            topology.add_connection(Connection(topology, host, endpoint))

    for i in range(number_of_benign_nodes):
        host = topology.add_benign_host(Host(topology, "b" + str(i), colour=benign_colour))
        for endpoint in endpoints:
            topology.add_connection(Connection(topology, host, endpoint))


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
def get_tree_topology(tree_shape: list, malicious, benign):
    if len(tree_shape) == 0:
        raise NetworkError("Cannot make empty internal network!")
    topology = Topology()
    core_switch = topology.add_switch(Switch(topology, colour="000000"))

    number_of_internal_nodes = len(topology.internal_hosts)

    # Create the internal network of the topology
    create_internal_network(tree_shape, core_switch, topology)

    if number_of_internal_nodes == len(topology.internal_hosts):
        warn("!!! Creating topology without an internal network !!!")

    # Create the external network of the topology
    number_of_malicious_nodes = malicious()
    number_of_benign_nodes = benign()

    if number_of_malicious_nodes + number_of_benign_nodes == 0:
        warn("!!! Creating topology without an external network !!!")

    for i in range(number_of_malicious_nodes):
        host = topology.add_malicious_host(Host(topology, "m" + str(i), colour='#F55B27'))
        topology.add_link(Link(topology, host, core_switch))

    for i in range(number_of_benign_nodes):
        host = topology.add_benign_host(Host(topology, "b" + str(i), colour="#07D962"))
        topology.add_link(Link(topology, host, core_switch))

    return topology


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
    core_checker = topology.add_checker(Checker(topology, colour='#f0f0f0', name="cc0"), 0) # core checker is black
    aggregator = topology.add_aggregator(Host(topology, colour='#000fff', name="agg0")) # aggregator is grey
    topology.add_link(Link(topology, aggregator, core_checker))

    number_of_checkers = topology.number_of_checkers()

    # Create the internal network
    create_checkers(net_shape, core_checker, topology, 1)

    if number_of_checkers == topology.number_of_checkers():
        warn("!!! Creating topology without an internal network !!!")

    # Create the external network of the topology
    build_external_network(benign, malicious, topology, '#07D962', '#F55B27', topology.get_endpoints())

    return topology


"""
Functions for the Arish Topology
"""

"""
Create the intermediary checkers. Tree-shape is a list of functions that return a number, layer denotes
the layer in the network (edge-router is layer 0). Used for graphing the network.

Recursively builds the checkers by repeatedly taking the next element in tree_shape, and creating that many
checkers in the next layer, per checker in the last layer. When tree_shape is empty, it creates the endpoints.

"""
def create_funnel_checkers(tree_shape: list, parent, topology, layer):
    if len(tree_shape) == 0:
        return

    temp = tree_shape[0]()
    for i in range(temp):
        checker = topology.add_checker(Checker(topology, colour="#FAC72F"), layer) # Internal checkers are yellow
        topology.add_connection(Connection(topology, checker, parent))
        create_funnel_checkers(tree_shape[1:], checker, topology, layer + 1)

"""
Creates n+1 endpoints for the funnel network, where n is the number of core routers on the top layer
(furthest away from the edge router into the internal network). Each endpoint is connected to the two
nearest indexed core routers, except for the first and last endpoint, which are connected only to the outer routers. 
"""
def create_funnel_endpoints(topology: ManyEndpointsTopology):
    connections = 2 # Each endpoint is connected with two switches (except the first and the last, which have only 1 connection)
    core_routers = topology.checkers[-1]

    # Edge case handling
    if len(core_routers) < 1:
        raise NetworkError("Cannot make empty funnel network!")
    if len(core_routers) == 1:
        switch = topology.add_endpoint(Host(topology, colour='#27ADF5')) # Endpoints are blue
        topology.add_connection(Connection(topology, switch, core_routers[0]))
        topology.add_connection(Connection(topology, switch, topology.get_aggregator()))
        return


    for i in range(len(core_routers) + 1):
        switch = topology.add_endpoint(Host(topology, colour='#27ADF5')) # Endpoints are blue
        topology.add_connection(Connection(topology, switch, topology.get_aggregator()))

    topology.add_connection(Connection(topology, topology.get_endpoints()[0], core_routers[0]))
    topology.add_connection(Connection(topology, topology.get_endpoints()[-1], core_routers[-1]))

    for i in range(1, len(topology.get_endpoints()) - 1):   # For each endpoint that isnt the first or last
        topology.add_connection(Connection(topology, topology.get_endpoints()[i], core_routers[i-1]))
        topology.add_connection(Connection(topology, topology.get_endpoints()[i], core_routers[i]))

"""
Creates a funnel network according to the net_shape, as well as malicious() and benign() external nodes.
malicious and benign are both expected to be lambdas that return a number.
net_shape is expected to be a list of such lambdas. 

Funnel network contains an edge router (which stands in front of the internal network) and an aggregator (which
performs data aggregation for the DDoS detection mechanism). From the edge router we build n layers of core routers, 
where n is the length of of net_shape. Each index of net_shape creates a new layer of core routers with 
net_shape[i]() core routers attached to its parent. For example:

get_entry_funnel_topology([lambda : 2, lambda : 3], lambda x : 2, lambda : 3) creates a network with:
- One edge router
- One aggregator
- Two core routers in the first layer, both connected to the edge router
- 6 (2 * 3) core routers in the second layer. Three of these are connected to the first router in layer 1, three
    are connected to the second router in layer 1. 
- 7 endpoints (border routers). The first and last are connected to the first and last core router on layer 2 respectively.
    Each other endpoint is connected to two routers on layer 2.
- 2 malicious and 3 benign external nodes, each connected to every endpoint. These represent "the internet".
- The aggregator is also connected to each endpoint. 
"""
def get_entry_funnel_topology(net_shape, malicious, benign):
    if len(net_shape) <= 0:
        raise NetworkError("Cannot make empty funnel network!")

    topology = ManyEndpointsTopology()
    core_checker = topology.add_checker(Checker(topology, colour='#f4f4f4', name="cc0"), 0)  # core checker is grey
    aggregator = topology.add_aggregator(Host(topology, colour='#000fff', name="agg0"))  # aggregator is blue
    topology.add_connection(Connection(topology, aggregator, core_checker))

    number_of_checkers = topology.number_of_checkers()

    # Create the internal network
    create_funnel_checkers(net_shape, core_checker, topology, 1)
    create_funnel_endpoints(topology)

    if number_of_checkers == topology.number_of_checkers():
        warn("!!! Creating topology without an internal network !!!")

    # Create the external network of the topology
    build_external_network(benign, malicious, topology, '#07D962', '#F55B27', topology.get_endpoints())

    return topology


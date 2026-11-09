import random

from mininet.log import setLogLevel
from experiments import test_topologies
from lib.aggregators.none_aggregator import NoneAggregator
from lib.experiment import Experiment

if __name__ == '__main__':
    # Tell mininet to print useful information
    setLogLevel('info')

    # Tree-topology
    # network = Experiment(test_topologies.get_tree_topology(
    #     [
    #         lambda : random.randint(2, 3),  # Core switch has 2-3 connections
    #         lambda : random.randint(1, 2),  # First layer switches have 1-2 connections
    #         lambda : 3                      # 3 stations at the leaves of the network
    #     ],
    #     lambda : random.randint(1, 2),  # Somewhere between 1 and 2 malicious nodes
    #     lambda : random.randint(2, 3),  # Somewhere between 2 and 3 benign nodes
    # ), NoneAggregator, None, [])

    # Distributed-topology
    # network = Experiment(test_topologies.get_distributed_topology(
    #     [               # 1 central checker
    #         lambda: 4,            # 4 checkers below the central checker
    #         lambda: 2,            # which in turn each have 2 checkers below them
    #         lambda: 2,            # which in turn each have 2 checkers below them
    #         lambda: 3             # which in turn each have 2 endpoints below them
    #     ],
    #     lambda : random.randint(3, 5),  # Somewhere between 3 and 5 malicious nodes
    #     lambda : random.randint(2, 4),  # Somewhere between 2 and 4 benign nodes
    # ), NoneAggregator(), None, [])

    # Funnel-topology
    # network = Experiment(test_topologies.get_entry_funnel_topology(
    #     [lambda : 2, lambda : 3], lambda : 2, lambda : 3
    # ), NoneAggregator(), None, [])

    network = Experiment(test_topologies.get_entry_funnel_topology(
        [lambda: 1], lambda: 1, lambda: 1
    ), None, None, "Test experiment")

    network.create_summary()

    # network.topology.show_visualisation()

    # network.start_net()

    # network.stop_net()

# DDoSDetection
Research repository into the detection of carpet bombing DDoS attacks

Requires you to set up an OVSwitch controller first, on address 127.0.0.1:6633.
If it doesn't work yet, try running `sudo /usr/share/openvswitch/scripts/ovs-ctl start`

When running experiment.py, use `sudo .venv/bin/python experiments/experiment.py`
If that's giving you trouble, try `sudo .venv/bin/python -m experiments.experiment`


# Code Classes Descriptions and Requirements

Experiments - Top level code - Is the runnable code
 - Type of topology
 - External behaviour - Attack traffic, normal traffic, etc.
 - Aggregations method / type
 - Mininet/network creator - Send topology etc. here
 - One run method running the whole experiment
  - Create a summary file of, what topology, traffic statistics, aggregation methods etc.

Topology - Topology recipe
 - List of types of nodes
    - Benign host - Normal host (Outside network)
    - Malicous host - DDoS host (Outside network)
    - Internal host - Includes truthful and malicious internal hosts descriped by a bool (eg. 1 for malicious, 0 for truthful)
 - Switches - List
 - Connections - List
 - Link objects - List (Links needs some arbitrary delay otherwise experiment will be hardware dependent)
 - Topology setup/recipe

 - Visualize topology
 - Build.network
 - Adders, Getters, removers methods

External behaviour - Handles outside traffic to inside (Benign and malicois hosts communication to internal hosts)
 - Behavior of benign hosts code
 - Behavior of malicious hosts code
 - get.statistics method - Relevant statistics about the nodes and their traffic
 - Run a chosen traffic behaviour for x time(Told by Experiment)
 - Behavior variables
    - Type of traffic
    - Duration (Could also be indefinitly)
    - Rate of traffic for each type

Internal behaviour - All internal hosts
 - Aggregator
 - extract data method
 - Map {host, type of host/what code will it use} Descripes what code it runs
 - extract_data method - Queries D-ITG for data.

Aggregator
 - increment
 - estimate
 - get_data
 - Aggregation method is created here
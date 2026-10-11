from lib.topologies.topology import Topology

class Network():
    def __init__(self, topology: Topology):
        self.tmp = 'tmp.txt'
        self.data = {}
        self.controller_ip = '192.168.1.26'
        self.controller_port = 6633
        self.topology = []

# Keep track of all nodes, access points, connections, etc.
# Way to start, way to shut down
# Should have a list of traffics (traffic is usually derived from a pcap. Can be malicious, doesn't have to be)
# Ideally has a way to visualise itself

# has a from_pcap() method to create it from a pcap
# has a from_topology() method that creates it from a topology



# PCAP -> Network + attack
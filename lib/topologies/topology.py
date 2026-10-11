from mininet.topo import Topo

class Topology(Topo):
    def __init__(self, *args, **params):
        super().__init__(*args, **params)
        self.data = {}
        self.access_points = []
        self.hosts = []
        self.switches = []
        self.links = []
        self.counters = {"hosts": 0, "switches": 0, "links": 0}


# Should define the entire network
# Try to figure out an easy way to create these?
# Store these networks in a database?
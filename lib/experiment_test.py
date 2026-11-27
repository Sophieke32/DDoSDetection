import os

from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.log import info
from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.util import dumpNodeConnections

from external_behaviour.external_behaviour import ExternalBehaviour
from internal_behaviour.internal_behaviour import InternalBehaviour
from topologies.many_endpoints_topology import ManyEndpointsTopology


POLL_INTERVAL = 1.0
LOG_INTERVAL = 1.0

class Experiment:
    outdir = os.path.abspath("results/")
    phases = [(20, 50), (20, 500), (20, 50)]
    sketch = []
    poll_interval = 1.0
    log_interval = 1.0

    def __init__(self, phases, sketch, name):
        self.outdir = self.outdir + name.replace(' ', '_')
        self.phases = phases
        self.sketch = sketch
        
    def run(self):
        setLogLevel("info")
        os.makedirs(self.outdir, exist_ok=True)

        topology = ManyEndpointsTopology.build_network()         # topology code builds (and starts) the network
        net = Mininet(
            topology=topology,
            switch=OVSBridge,
            controller=None,
            build=False
        )

        internal = InternalBehaviour(
            net,
            edge_hosts=topology.get_edge_router(),
            internal_hosts=topology.get_all_checkers().remove(topology.get_edge_router()),
            outdir=self.outdir,
            sketch=self.sketch,
            poll_interval=self.poll_interval,
            log_interval=self.log_interval)

        external = ExternalBehaviour(
            net,
            topology.benign_external_hosts,
            topology.malicious_external_hosts,
            topology.edge[0],
            self.phases)

        info('\n### Host connections ###\n')
        dumpNodeConnections(net.hosts)

        info('\n### Network is built, testing connectivity... ###\n')
        net.pingAll()
        CLI(self.net)

        internal.start() # routing + agents + ITGRecv on the edge host

        os.chdir(self.outdir) # ITGSend writes its logs relative to cwd
        try:
            external.start() # blocks until all phases are done
        finally:
            internal.stop()
            net.stop()
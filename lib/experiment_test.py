import os

from mininet.log import setLogLevel
from mininet.cli import CLI
from mininet.log import info
from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.util import dumpNodeConnections
from topologies.topology import Topology

from external_behaviour.external_behaviour import ExternalBehaviour
from internal_behaviour.internal_behaviour import InternalBehaviour

# Everything that needs to change between experiments should be here
OUTDIR = os.path.abspath("results/expTest")   # name of the experiment, results go here
PHASES = [(20, 50), (20, 500), (20, 50)]      # (duration s, packets/s), first phase is benign
SKETCH = []                                   # which sketches/aggregations to run
POLL_INTERVAL = 1.0                           # edge requests sketch data this often
LOG_INTERVAL = 1.0                            # every internal host logs metrics this often


def main():
    setLogLevel("info")
    os.makedirs(OUTDIR, exist_ok=True)

    topology = Topology.build_network()         # topology code builds (and starts) the network
    net = Mininet(
        topology=topology,
        switch=OVSBridge,
        controller=None,
        build=False
    )

    internal = InternalBehaviour(
        net,
        edge_hosts=topology.edge,
        core_hosts=topology.core,
        border_hosts=topology.border,
        outdir=OUTDIR,
        sketch=SKETCH,
        poll_interval=POLL_INTERVAL,
        log_interval=LOG_INTERVAL)
    
    external = ExternalBehaviour(
        net,
        topology.benign_external_hosts,
        topology.malicious_external_hosts,
        topology.edge[0],
        PHASES)

    info('\n### Host connections ###\n')
    dumpNodeConnections(net.hosts)

    info('\n### Network is built, testing connectivity... ###\n')
    net.pingAll()
    CLI(self.net)

    internal.start() # routing + agents + ITGRecv on the edge host

    os.chdir(OUTDIR) # ITGSend writes its logs relative to cwd
    try:
        external.start() # blocks until all phases are done
    finally:
        internal.stop()
        net.stop()


if __name__ == "__main__":
    main()
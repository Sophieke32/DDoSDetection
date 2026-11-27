import os
import time
from collections import deque

from internal_behaviour.router import Router
from internal_behaviour.edge import Edge


class InternalBehaviour:
    def __init__(
        self,
        net,
        edge_hosts: list,
        internal_hosts: list,
        outdir: str = "results",
        sketch: list = None,
        poll_interval: float = 1.0,
        log_interval: float = 1.0,
        reset_on_poll: bool = True,
        start_itg_recv: bool = True):


        self.net = net
        self.edge_host = edge_hosts[0]
        self.internal_hosts = internal_hosts
        self.outdir = os.path.abspath(outdir)
        self.sketch = sketch or []
        self.poll_interval = poll_interval
        self.log_interval = log_interval
        self.reset_on_poll = reset_on_poll
        self.start_itg_recv = start_itg_recv

        self.roles = {self.edge_host.name: "edge"}

        self.routers = []
        self.edge = None
        self._discover()

    # Topology discovery
    @staticmethod
    def _peers(host):
        for interface in host.intfList():
            link = interface.link
            if link is None:
                continue
            yield interface, (link.intf2 if link.intf1 is interface else link.intf1)

    def _discover(self): # Finds each hosts neighbors, and who to send data to(uplink)
        self.adj = {n: [] for n in self.hosts}
        for name, host in self.hosts.items():
            for interface, peer in self._peers(host):
                if peer.node.name in self.hosts:
                    self.adj[name].append((interface, peer, peer.node.name))

        # distance to edge router
        self.dist = {self.edge_host.name: 0}
        queue = deque([self.edge_host.name])
        while queue:
            cur = queue.popleft()
            for _, _, nxt in self.adj[cur]:
                if nxt not in self.dist:
                    self.dist[nxt] = self.dist[cur] + 1
                    queue.append(nxt)

        # Picks first neighbor that is closer to the edge
        self.uplink = {}
        for name in self.hosts:
            if name == self.edge_host.name:
                continue
            for interface, peer, nxt in self.adj[name]:
                if self.dist[nxt] < self.dist[name]:
                    self.uplink[name] = (interface, peer)
                    break

    def _first_hops(self, src):
        hops, seen, queue = {}, {src}, deque([src])
        while queue:
            cur = queue.popleft()
            for interface, peer, nxt in self.adj[cur]:
                if nxt in seen:
                    continue
                seen.add(nxt)
                hops[nxt] = (interface, peer) if cur == src else hops[cur]
                queue.append(nxt)
        return hops

    # routing/packet fowarding
    def _configure_routing(self):
        destinations = []                        # (ip, owning internal node)
        for name, host in self.hosts.items():
            for interface, peer in self._peers(host):
                if interface.IP():
                    destinations.append((interface.IP(), name))
                if peer.node.name not in self.hosts and peer.IP():
                    destinations.append((peer.IP(), name))

        for name, host in self.hosts.items():
            host.cmd("sysctl -w net.ipv4.ip_forward=1")
            host.cmd("sysctl -w net.ipv4.conf.all.rp_filter=0")
            host.cmd("sysctl -w net.ipv4.conf.default.rp_filter=0")
            for interface in host.intfList():
                host.cmd(f"sysctl -w net.ipv4.conf.{interface.name}.rp_filter=0")

            if name in self.uplink:
                interface, peer = self.uplink[name]
                if peer.IP():
                    host.cmd(f"ip route replace default via {peer.IP()} dev {interface.name}")

            hops = self._first_hops(name)
            for ip, owner in destinations:
                hop = hops.get(owner)
                if owner == name or hop is None:
                    continue
                interface, peer = hop
                if not peer.IP() or ip == peer.IP():
                    continue
                host.cmd(f"ip route replace {ip}/32 via {peer.IP()} dev {interface.name}")

    def _interfaces(self, host): # Returns all the interfaces, and the ingress interfaces (packets through these are tracked)
        all_interfaces = [i.name for i in host.intfList()]
        up = self.uplink.get(host.name)
        ingress = [n for n in all_interfaces if not (up and n == up[0].name)]
        return ingress, all_interfaces

    def start(self):
        os.makedirs(self.outdir, exist_ok=True)
        
        self._configure_routing()

        for host in self.internal_hosts:
            ingress, all_interfaces = self._interfaces(host)
            self.routers.append(Router(host, self.roles[host.name], ingress, all_interfaces, self.outdir, self.sketch, self.log_interval))
        ingress, all_interfaces = self._interfaces(self.edge_host)
        self.edge = Edge(self.edge_host, ingress, all_interfaces, self.outdir, self.routers,
                        self.sketch, self.log_interval, self.poll_interval,
                        self.reset_on_poll, self.start_itg_recv)

        for router in self.routers:
            router.start()
        time.sleep(1.0)
        self.edge.start()
        time.sleep(1.0) # wait for ITGRecv to start before sending traffic or externals stop after a single packet

    def stop(self):
        if self.edge:
            self.edge.stop()
        for router in self.routers:
            router.stop()
from mininet.topo import Topo


class CompanyTopo(Topo):
    def build(self, users=9):
        # Company distribution and core.
        s1 = self.addSwitch("s1")
        s2 = self.addSwitch("s2")
        core = self.addSwitch("s3")

        # Three company-facing gateways.
        company_gws = []
        for i in range(1, 4):
            gw = self.addSwitch(f"cgw{i}")
            company_gws.append(gw)

        # Every external user has an individual gateway bridge.
        # Assign external gateways round-robin to the three company gateways.
        for i in range(1, users + 1):
            user = self.addHost(f"user{i}", ip=f"10.0.0.{10+i}/24")
            ext_gw = self.addSwitch(f"egw{i}")
            self.addLink(user, ext_gw)
            self.addLink(ext_gw, company_gws[(i - 1) % 3])

        # Company gateway uplinks into the distribution layer.
        self.addLink(company_gws[0], s1)
        self.addLink(company_gws[1], s1)
        self.addLink(company_gws[2], s2)

        # Two distribution switches converge at the core.
        self.addLink(s1, core)
        self.addLink(s2, core)

        # Monitoring hosts: m1/m2 observe s1; m2/m3 observe s2.
        # m2 is deliberately dual-homed and records both interfaces.
        self.addHost("mon1", ip="10.0.0.201/24")
        self.addHost("mon2", ip="10.0.0.202/24")
        self.addHost("mon3", ip="10.0.0.203/24")
        self.addLink("mon1", s1)
        self.addLink("mon2", s1)
        self.addLink("mon2", s2)
        self.addLink("mon3", s2)

        # Central target.
        self.addHost("target", ip="10.0.0.100/24")
        self.addLink("target", core)


topos = {"company": lambda: CompanyTopo()}

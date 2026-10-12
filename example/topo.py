from mininet.topo import Topo

class CustomTopology(Topo):
    def build(self):
        #Add one root switch and two more on the first level
        switch1 = self.addSwitch('s1', protocols='OpenFlow13')
        switch2 = self.addSwitch('s2', protocols='OpenFlow13')
        switch3 = self.addSwitch('s3', protocols='OpenFlow13')

        #Add links between root switch and the other two
        self.addLink(switch1, switch2)
        self.addLink(switch1, switch3)
        self.addLink(switch2, switch3)

        #Add hosts
        host1 = self.addHost('h1')
        host2 = self.addHost('h2')
        host3 = self.addHost('h3')
        host4 = self.addHost('h4')

        #Links hosts and first level switches
        self.addLink(host1, switch2)
        self.addLink(host2, switch2)
        self.addLink(host3, switch3)
        self.addLink(host4, switch3)
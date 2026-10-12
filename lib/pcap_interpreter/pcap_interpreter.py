# ToDo: Write logic that can turn a PCAP file into a Topology and a Traffic object

# Consider looking at:
# https://github.com/smythtech/mininet_pcap_replay/blob/master/mininet_pcap_replay.py#L235

import csv
from lib.topologies.topology import Topology
from lib.topologies.host import Host
from lib.topologies.switch import Switch
from lib.topologies.link import Link

ip_address_headers = ["ip src", "ip dst", "source ip", "destination ip"]

# Given the header in a csv file, looks for columns with ip addresses
def find_ip_addresses(row):
    res = []
    for i in range(len(row)):
        if row[i].lower() in ip_address_headers:
            res.append(i)

    return res

def get_ip_addresses(row, indices, addresses):
    for i in indices:
        addresses.add(row[i])

def pcap_to_network(path):
    hosts = {}
    addresses = set()
    with open(path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        ip_address_colum_indices = find_ip_addresses(header)

        for row in reader:
            get_ip_addresses(row, ip_address_colum_indices, addresses)

        # Create a dict for each host (indexed by IP address), so we can
        # add more fields to each host as we continue development
        for i in addresses:
            hosts[i] = {}

    topology = Topology()

    # Create a switch in the middle of the network. Every host is connected with this switch
    spider = Switch(topology, name="spider")
    topology.add_switch(spider)

    for key, value in hosts.items():
        host = Host(topology, ip=key)
        topology.add_host(host)
        topology.add_link(Link(topology, host, spider))

    return topology

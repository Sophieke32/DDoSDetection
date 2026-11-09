from lib.topologies.host import Host
from lib.topologies.link import Link
from lib.topologies.switch import Switch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from topology import Topology


class Connection:
    src: Host
    dst: Host
    src_link: Link
    dst_link: Link
    switch: Switch

    def __init__(self, topology: Topology, src: Host, dst: Host):
        self.src = src
        self.dst = dst
        switch_name = "switch_" + src.name + "_" + dst.name
        self.switch = Switch(topology, name=switch_name, connection=True)
        self.src_link = Link(topology, self.src, self.switch, connection=True)
        self.dst_link = Link(topology, self.dst, self.switch, connection=True)

    def get_src(self):
        return self.src

    def get_src_link(self):
        return self.src_link

    def get_dst(self):
        return self.dst

    def get_dst_link(self):
        return self.dst_link

    def get_switch(self):
        return self.switch


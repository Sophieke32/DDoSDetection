from abc import ABC

from mininet.net import Mininet


class Traffic(ABC):
    def __init__(self):
        pass

    def start(self, network: Mininet):
        pass

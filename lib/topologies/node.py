from abc import ABC, abstractmethod

from lib.topologies.no_mn_representation_error import NoMNRepresentationError


class Node(ABC):
    def __init__(self):
        self.data = {}
        self.ip = '192.168.1.26'
        self.mac = "AA:AA:AA:AA:AA"
        self.connections = []
        self.name = self.generate_name()
        self.mn_representation = None

    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def generate_name(self):
        pass

    def __get_mn_representation__(self):
        if self.mn_representation is None:
            raise NoMNRepresentationError(self.name + " hasn't been created in mininet yet.")
        else:
            return self.mn_representation

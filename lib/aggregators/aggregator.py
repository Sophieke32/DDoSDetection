from abc import ABC, abstractmethod


class Aggregator(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def increment(self, e):
        pass

    @abstractmethod
    def estimate(self, e):
        pass

    @abstractmethod
    def get_data(self):
        pass
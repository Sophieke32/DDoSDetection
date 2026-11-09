from lib.aggregators.aggregator import Aggregator


class NoneAggregator(Aggregator):

    def __init__(self):
        super().__init__()

    def increment(self, e):
        pass

    def estimate(self, e):
        pass


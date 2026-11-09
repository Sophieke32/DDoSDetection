import math
import numpy as np

from lib.aggregators.aggregator import Aggregator


class CountMinSketch(Aggregator):
    w = 0,
    d = 0,
    epsilon = 0,
    delta = 0,
    table = None
    hashes = []

    def __init__(self, accuracy, confidence, hash_function_generator):
        super().__init__()
        self.epsilon = accuracy # Smaller is more accurate
        self.delta = confidence # Smaller is more confidence
        self.d = math.ceil(math.log(math.pow(self.delta, -1.0)))
        self.w = math.ceil(math.e * math.pow(self.epsilon, -1.0))
        self.table = np.zeros((self.d, self.w))

        for i in range(self.d):
            self.hashes.append(hash_function_generator.generate(self.w))

    def increment(self, e):
        for i in range(self.d):
            self.table[i][self.hashes[i](e)] += 1

    def estimate(self, e):
        res = self.table[0][self.hashes[0](e)]
        for i in range(1, self.d):
            val = self.table[i][self.hashes[i](e)]
            if val < res:
                res = val

        return res

    def get_data(self):
        return self.table, self.hashes
a
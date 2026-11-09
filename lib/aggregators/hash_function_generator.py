import random
import math

class HashFunctionGenerator:
    LARGE_PRIME = 18446744073709551557

    def __init__(self, accuracy):
        self.m = math.ceil(math.e * math.pow(accuracy, -1))
        self.a_set = {None, }
        self.b_set = {None, }

    def generate(self, m):
        a = None
        b = None

        while a in self.a_set:
            a = random.randint(1, self.LARGE_PRIME - 1)

        while b in self.b_set:
            b = random.randint(0, self.LARGE_PRIME - 1)

        self.a_set.add(a)
        self.b_set.add(b)

        return lambda x : ((a * x + b) % self.LARGE_PRIME) % m

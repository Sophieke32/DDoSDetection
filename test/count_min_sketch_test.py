import unittest
from hypothesis import given, strategies as st
from lib.aggregators.count_min_sketch import CountMinSketch
from lib.aggregators.hash_function_generator import HashFunctionGenerator

class CountMinSketchTest(unittest.TestCase):

    def test_one_increase(self):
        accuracy = 0.1
        cms = CountMinSketch(accuracy, 0.01, HashFunctionGenerator(accuracy))

        cms.increment(1)

        self.assertEqual(cms.estimate(1), 1)

    # Asserts that there will be collisions
    def test_flaky(self):
        accuracy = 0.1
        cms = CountMinSketch(accuracy, 0.01, HashFunctionGenerator(accuracy))

        for i in range(100):
            cms.increment(i)

        for i in range(100):
            self.assertNotEqual(cms.estimate(i), 1)

    # Property based testing, runs test for a variety of values of n between 1 and 1000000
    @given(st.integers(min_value=1, max_value=1000000))
    def test_arbitrary_increase(self, n):
        accuracy = 0.1
        cms = CountMinSketch(accuracy, 0.01, HashFunctionGenerator(accuracy))

        print(n)

        for i in range(n):
            cms.increment(1)

        self.assertEqual(cms.estimate(1), n)


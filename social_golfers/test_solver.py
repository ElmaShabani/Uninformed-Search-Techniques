"""Tests for solutions, exhaustive search, and DFS resource limits."""
import unittest

from model import valid
from solver import solve


class SolverTests(unittest.TestCase):
    def test_original_players(self):
        result = solve(8, 4, 3)
        self.assertEqual(result["status"], "solved")
        self.assertTrue(valid(result["schedule"], 8, 4, 3))

    def test_small_saturated_instance(self):
        result = solve(3, 3, 4)
        self.assertEqual(result["status"], "solved")
        self.assertTrue(valid(result["schedule"], 3, 3, 4))

    def test_first_week_needs_no_search(self):
        result = solve(8, 4, 1, max_nodes=0)
        self.assertEqual(result["status"], "solved")
        self.assertTrue(valid(result["schedule"], 8, 4, 1))

    def test_theoretical_bound(self):
        result = solve(8, 4, 11)
        self.assertEqual(result["status"], "unsatisfiable")
        self.assertIsNone(result["schedule"])

    def test_exhaustion_below_bound(self):
        # With 2 groups of 3, every group in the next week must repeat a pair.
        result = solve(2, 3, 2)
        self.assertEqual(result["status"], "unsatisfiable")
        self.assertGreater(result["stats"]["backtracks"], 0)

    def test_limits_are_not_unsatisfiability(self):
        for limits in ({"max_nodes": 0}, {"timeout": 0}):
            with self.subTest(limits=limits):
                result = solve(8, 4, 3, **limits)
                self.assertEqual(result["status"], "limit")
                self.assertIsNone(result["schedule"])

    def test_invalid_parameters(self):
        for params in ((0, 4, 3), (8, 1, 3), (8, 4, 0)):
            with self.subTest(params=params):
                with self.assertRaises(ValueError):
                    solve(*params)


if __name__ == "__main__":
    unittest.main()

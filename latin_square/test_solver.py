"""Tests for Latin Square constraints, iterative deepening, and backtracking."""
import unittest

from model import landscape, objective, valid
from solver import solve


class LatinSquareTests(unittest.TestCase):
    def test_solutions_and_depth_limits(self):
        for n in (1, 2, 3, 5):
            with self.subTest(n=n):
                result = solve(n)
                self.assertEqual(result["status"], "solved")
                self.assertTrue(valid(result["grid"]))
                self.assertEqual(objective(result["grid"]), 0)
                self.assertEqual(
                    [step["depth_limit"] for step in result["iterations"]],
                    list(range(n * n + 1)),
                )

    def test_backtracking_is_used(self):
        result = solve(5)
        self.assertGreater(result["stats"]["backtracks"], 0)
        self.assertTrue(valid(result["grid"]))

    def test_resource_limits(self):
        for limits in ({"max_nodes": 0}, {"timeout": 0}):
            with self.subTest(limits=limits):
                result = solve(3, **limits)
                self.assertEqual(result["status"], "limit")
                self.assertIsNone(result["grid"])

    def test_invalid_size(self):
        for n in (0, -1):
            with self.assertRaises(ValueError):
                solve(n)

    def test_landscape_counts(self):
        # A relaxed 2x2 tree has 1 + 2 + 4 + 8 + 16 nodes.
        self.assertEqual(landscape(2)["unpruned_tree_nodes"], 31)
        self.assertEqual(landscape(5)["complete_assignments"], 5 ** 25)

    def test_objective_and_constraints(self):
        self.assertEqual(objective([[0, 0], [0, 0]]), 4)
        self.assertGreater(objective([[1, 1], [2, 2]]), 0)
        self.assertFalse(valid([[1, 1], [2, 2]]))
        self.assertFalse(valid([[1, 2], [1, 2]]))
        self.assertFalse(valid([[1, 2]]))
        with self.assertRaises(ValueError):
            objective([[1, 2]])


if __name__ == "__main__":
    unittest.main()

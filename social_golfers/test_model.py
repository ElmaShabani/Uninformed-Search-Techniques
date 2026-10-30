"""Tests for the model and state space counts."""

import unittest
from itertools import combinations

from model import landscape, objective, upper_bound, valid


class ModelTests(unittest.TestCase):
    def test_partitions_against_enumeration(self):
        # All partitions of four players into two unordered pairs.
        players = set(range(4))
        partitions = set()
        for pair in combinations(players, 2):
            other = tuple(sorted(players - set(pair)))
            partitions.add(tuple(sorted((pair, other))))
        result = landscape(2, 2, 2)
        self.assertEqual(result["partitions_per_week"], len(partitions))
        self.assertEqual(result["weekly_capacity_valid_schedules"], 9)
        self.assertEqual(result["after_fixing_week_one"], 3)
        self.assertEqual(result["variables"], 8)
        self.assertEqual(result["raw_assignments"], 256)

    def test_fixed_first_week(self):
        self.assertEqual(landscape(8, 4, 1)["after_fixing_week_one"], 1)
        self.assertEqual(upper_bound(8, 4), 10)

    def test_invalid_parameters(self):
        for params in ((0, 4, 1), (8, 1, 1), (8, 4, 0)):
            with self.subTest(params=params):
                with self.assertRaises(ValueError):
                    landscape(*params)

    def test_valid_schedule(self):
        schedule = [[[0, 1], [2, 3]], [[0, 2], [1, 3]]]
        self.assertTrue(valid(schedule, 2, 2, 2))
        self.assertEqual(objective(schedule), 0)

    def test_repeated_pairs_and_missing_players(self):
        week = [[0, 1], [2, 3]]
        self.assertEqual(objective([week, week]), 2)
        self.assertFalse(valid([week, week], 2, 2, 2))
        self.assertFalse(valid([[[0, 1], [1, 3]]], 2, 2, 1))


if __name__ == "__main__":
    unittest.main()

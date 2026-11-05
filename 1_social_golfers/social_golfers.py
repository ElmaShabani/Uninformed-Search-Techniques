"""Initial model for the Social Golfers problem.

The variable x[week, player] assigns a player to a group for that week.
The domain is {0, ..., g-1}; players are numbered from 0 to g*p-1.
Each group contains p players, and no pair may meet more than once.
The schedule is a list of weeks, each containing g lists of players.

Social Golfers using DFS with backtracking.

Run: python3 1_social_golfers/social_golfers.py --groups 8 --size 4 --weeks 3
The theoretical week bound does not guarantee that DFS finds a schedule within the time limit.

REFERENCE_SCHEDULE is attributed reference data, not a DFS result."""
from dataclasses import dataclass, asdict
from time import perf_counter
from itertools import combinations
from math import factorial
import argparse
import unittest


REFERENCE_SOURCE = 'Alejandro Aguado, A 10 Days Solution to the Social Golfer Problem: https://www.mathpuzzle.com/MAA/54-Golf%20Tournaments/socgolf1.pdf'


REFERENCE_SCHEDULE = [[[0, 1, 2, 3], [4, 5, 22, 23], [6, 7, 20, 21], [8, 25, 26, 27], [9, 10, 11, 24], [12, 13, 15, 30], [14, 28, 29, 31], [16, 17, 18, 19]], [[0, 4, 8, 28], [1, 6, 18, 23], [2, 7, 17, 22], [3, 5, 26, 31], [9, 13, 14, 27], [10, 15, 19, 21], [11, 25, 29, 30], [12, 16, 20, 24]], [[0, 11, 14, 21], [1, 7, 10, 28], [2, 15, 20, 25], [3, 13, 22, 24], [4, 9, 18, 31], [5, 16, 27, 30], [6, 8, 19, 29], [12, 17, 23, 26]], [[0, 18, 24, 27], [1, 9, 19, 26], [2, 8, 11, 16], [3, 10, 17, 25], [4, 7, 12, 29], [5, 6, 14, 15], [13, 20, 23, 28], [21, 22, 30, 31]], [[0, 6, 13, 26], [1, 4, 11, 15], [2, 9, 21, 28], [3, 8, 14, 23], [5, 12, 18, 25], [7, 19, 24, 30], [10, 16, 22, 29], [17, 20, 27, 31]], [[0, 7, 25, 31], [1, 5, 24, 29], [2, 12, 14, 19], [3, 18, 28, 30], [4, 6, 10, 27], [8, 13, 17, 21], [9, 15, 16, 23], [11, 20, 22, 26]], [[0, 5, 19, 20], [1, 14, 22, 25], [2, 23, 27, 29], [3, 4, 16, 21], [6, 9, 17, 30], [7, 11, 13, 18], [8, 10, 12, 31], [15, 24, 26, 28]], [[0, 15, 17, 29], [1, 13, 16, 31], [2, 4, 26, 30], [3, 6, 11, 12], [5, 7, 8, 9], [10, 14, 18, 20], [19, 22, 27, 28], [21, 23, 24, 25]], [[0, 9, 12, 22], [1, 8, 20, 30], [2, 5, 10, 13], [3, 7, 15, 27], [4, 14, 17, 24], [6, 16, 25, 28], [11, 19, 23, 31], [18, 21, 26, 29]], [[0, 10, 23, 30], [1, 12, 21, 27], [2, 6, 24, 31], [3, 9, 20, 29], [4, 13, 19, 25], [5, 11, 17, 28], [7, 14, 16, 26], [8, 15, 18, 22]]]


class SearchLimit(RuntimeError):
    """Reaching a resource limit does not prove that the problem has no solution."""


@dataclass
class Stats:
    expanded: int = 0
    generated: int = 0
    backtracks: int = 0
    max_frontier: int = 0
    seconds: float = 0.0

    def dictionary(self):
        return asdict(self)


class Budget:
    def __init__(self, stats, max_nodes=200_000, timeout=20.0):
        self.stats = stats
        self.max_nodes = max_nodes
        self.timeout = timeout
        self.start = perf_counter()

    def tick(self):
        if self.max_nodes is not None and self.stats.expanded >= self.max_nodes:
            raise SearchLimit("The node limit was reached; feasibility remains unknown.")
        if self.timeout is not None and perf_counter() - self.start >= self.timeout:
            raise SearchLimit("The time limit was reached; feasibility remains unknown.")
        self.stats.expanded += 1

    def finish(self):
        self.stats.seconds = perf_counter() - self.start


def upper_bound(g, p):
    """Each player meets p-1 new players per week out of g*p-1 other players."""
    if g < 1 or p < 2:
        raise ValueError("Expected g >= 1 and p >= 2.")
    return (g * p - 1) // (p - 1)


def landscape(g, p, w):
    """Search space sizes before checking for repeated pairs.

    Groups are treated as unordered when counting weekly partitions.
    These sizes do not count schedules that satisfy all constraints.
    """
    bound = upper_bound(g, p)
    if w < 1:
        raise ValueError("The number of weeks must be positive.")
    n = g * p
    # Remove permutations within each group and permutations of the groups.
    partitions = factorial(n) // (factorial(p) ** g * factorial(g))
    return {
        "variables": n * w,
        "raw_assignments": g ** (n * w),
        "partitions_per_week": partitions,
        "weekly_capacity_valid_schedules": partitions ** w,
        "after_fixing_week_one": partitions ** (w - 1),
        "upper_bound_weeks": bound,
    }


def objective(schedule):
    """Minimize repeated meetings; a valid schedule has an objective value of 0."""
    seen = set()
    repeats = 0
    for week in schedule:
        for group in week:
            for pair in combinations(sorted(group), 2):
                if pair in seen:
                    repeats += 1
                seen.add(pair)
    return repeats


def valid(schedule, g, p, w):
    """Check weeks, group sizes, player participation, and repeated pairs."""
    upper_bound(g, p)
    if w < 1 or len(schedule) != w:
        return False
    expected = list(range(g * p))
    for week in schedule:
        if len(week) != g or any(len(group) != p for group in week):
            return False
        if sorted(player for group in week for player in group) != expected:
            return False
    return objective(schedule) == 0


def solve(g=8, p=4, w=3, max_nodes=200_000, timeout=20.0):
    bound = upper_bound(g, p)
    if w < 1:
        raise ValueError("w must be positive.")
    stats = Stats()
    budget = Budget(stats, max_nodes, timeout)
    if w > bound:
        budget.finish()
        return {"status": "unsatisfiable", "schedule": None,
                "reason": "The theoretical upper bound on weeks is exceeded.", "stats": stats.dictionary()}
    n = g * p
    # Relabeling players fixes the first week without losing solutions.
    schedule = [[list(range(k * p, (k + 1) * p)) for k in range(g)]]
    seen = {pair for group in schedule[0] for pair in combinations(group, 2)}

    def next_week():
        if len(schedule) == w:
            return True
        groups = [[] for _ in range(g)]
        schedule.append(groups)
        if place(0, groups):
            return True
        schedule.pop()
        return False

    def place(player, groups):
        budget.tick()
        if player == n:
            return next_week()
        for group in groups:
            if len(group) == p:
                continue
            pairs = [(other, player) for other in group]
            if any(pair in seen for pair in pairs):
                continue
            was_empty = not group
            group.append(player)
            seen.update(pairs)
            stats.generated += 1
            if place(player + 1, groups):
                return True
            # Undo the assignment: restore both the group and the recorded pairs.
            group.pop()
            seen.difference_update(pairs)
            stats.backtracks += 1
            # Empty groups are symmetric, so only the first one is tried.
            if was_empty:
                break
        return False

    try:
        found = next_week()
        status, reason = ("solved", "A valid schedule was found.") if found else (
            "unsatisfiable", "The search space was exhausted.")
    except SearchLimit as exc:
        found, status, reason = False, "limit", str(exc)
    budget.finish()
    return {"status": status, "schedule": schedule if found else None,
            "reason": reason, "stats": stats.dictionary()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groups", type=int, default=8)
    parser.add_argument("--size", type=int, default=4)
    parser.add_argument("--weeks", type=int, default=3)
    parser.add_argument("--max-nodes", type=int, default=200_000)
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()
    result = solve(args.groups, args.size, args.weeks, args.max_nodes, args.timeout)
    print("Status:", result["status"])
    for i, week in enumerate(result.get("schedule") or [], 1):
        print(f"Week {i}: " + " | ".join(",".join(map(str, group)) for group in week))
    if "stats" in result:
        print(result["reason"], result["stats"])
    print("Landscape:", landscape(args.groups, args.size, args.weeks))


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
    import sys
    if "--test" in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        main()

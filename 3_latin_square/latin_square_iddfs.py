"""Latin Square constraint model.

Each of the n*n cells is a variable with domain 1..n; 0 denotes an empty cell.
Every row and column must contain each domain value exactly once.
States are lists of n rows. The objective counts empty cells and duplicates.
Landscape counts ignore constraints and are not counts of valid Latin squares.

Latin Square using iterative deepening DFS and backtracking.

Run: python3 3_latin_square/latin_square_iddfs.py 5
Depth limits increase from 0 through n*n. A failed assignment is undone before
trying the next value. The first row and column are fixed to break symmetry."""
from dataclasses import dataclass, asdict
from time import perf_counter
import argparse
import unittest


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


def valid(grid):
    n = len(grid)
    target = set(range(1, n + 1))
    return n > 0 and all(len(row) == n and set(row) == target for row in grid) and all(
        {grid[r][c] for r in range(n)} == target for c in range(n))


def objective(grid):
    """Minimize empty cells and repeated values in rows and columns."""
    n = len(grid)
    if n < 1 or any(len(row) != n or any(type(v) is not int or not 0 <= v <= n
                                        for v in row) for row in grid):
        raise ValueError("The grid must be n by n with integer values in 0..n.")
    penalty = sum(row.count(0) for row in grid)
    units = grid + [[grid[r][c] for r in range(n)] for c in range(n)]
    for unit in units:
        values = [v for v in unit if v]
        penalty += len(values) - len(set(values))
    return penalty


def landscape(n):
    if n < 1:
        raise ValueError("n must be positive.")
    return {"variables": n * n, "domain_size": n,
            "complete_assignments": n ** (n * n),
            "unpruned_tree_nodes": sum(n ** k for k in range(n * n + 1))}


def solve(n=3, max_nodes=500_000, timeout=20.0):
    landscape(n)
    grid = [[0] * n for _ in range(n)]
    rows = [set() for _ in range(n)]
    cols = [set() for _ in range(n)]
    stats = Stats()
    budget = Budget(stats, max_nodes, timeout)
    iterations = []

    def dls(index, limit):
        budget.tick()
        if index == n * n:
            return True
        if index == limit:
            return False
        r, c = divmod(index, n)
        # Symmetry breaking: any Latin square can be reduced to this form.
        values = [c + 1] if r == 0 else ([r + 1] if c == 0 else range(1, n + 1))
        for value in values:
            if value in rows[r] or value in cols[c]:
                continue
            grid[r][c] = value
            rows[r].add(value)
            cols[c].add(value)
            stats.generated += 1
            if dls(index + 1, limit):
                return True
            grid[r][c] = 0
            rows[r].remove(value)
            cols[c].remove(value)
            stats.backtracks += 1
        return False

    try:
        status = "unsatisfiable"
        for limit in range(n * n + 1):
            before = stats.expanded
            found = dls(0, limit)
            iterations.append({"depth_limit": limit, "expanded": stats.expanded - before})
            if found:
                status = "solved"
                break
    except SearchLimit:
        status = "limit"
    budget.finish()
    return {"status": status, "grid": grid if status == "solved" else None,
            "iterations": iterations, "stats": stats.dictionary()}


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
    import sys
    if "--test" in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("n", type=int, nargs="?", default=3)
        parser.add_argument("--max-nodes", type=int, default=500_000)
        parser.add_argument("--timeout", type=float, default=20)
        args = parser.parse_args()
        result = solve(args.n, args.max_nodes, args.timeout)
        print("Status:", result["status"])
        for row in result["grid"] or []:
            print(*row)
        print("Iterations:", result["iterations"])
        print("Statistics:", result["stats"])
        print("Landscape:", landscape(args.n))

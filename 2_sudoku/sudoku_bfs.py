"""Sudoku constraint model.

Variables are the 81 cells; empty cells have domains drawn from 1..9.
A tuple of 81 integers represents a state, with 0 marking an empty cell.
Rows, columns, and 3x3 boxes must each contain distinct nonzero values.
The objective counts empty cells and duplicate values in all 27 units.
Landscape counts are relaxed search space sizes, not valid solution counts.

Sudoku using FIFO breadth-first search and optional DFS backtracking.

Run: python3 2_sudoku/sudoku_bfs.py --level easy
BFS reconstructs its path through parent links. Recursive backtracking is
provided separately through --method dfs. Optional naked-single propagation
applies constraint deductions without heuristic ordering of search choices."""
from dataclasses import dataclass, asdict
from time import perf_counter
import argparse
from collections import deque
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


UNITS = ([tuple(r * 9 + c for c in range(9)) for r in range(9)]
         + [tuple(r * 9 + c for r in range(9)) for c in range(9)]
         + [tuple((br + r) * 9 + bc + c for r in range(3) for c in range(3))
            for br in (0, 3, 6) for bc in (0, 3, 6)])


PEERS = [set().union(*(set(unit) for unit in UNITS if i in unit)) - {i}
         for i in range(81)]


def parse(rows):
    if len(rows) != 9 or any(len(row) != 9 for row in rows):
        raise ValueError("Sudoku must have 9 rows of 9 cells.")
    try:
        state = tuple(int(x) for row in rows for x in row)
    except (ValueError, TypeError) as exc:
        raise ValueError("Use digits 0..9; 0 represents an empty cell.") from exc
    validate(state)
    return state


def validate(state):
    if len(state) != 81 or any(type(x) is not int or not 0 <= x <= 9 for x in state):
        raise ValueError("A state must contain 81 integers from 0 to 9.")
    for unit in UNITS:
        filled = [state[i] for i in unit if state[i]]
        if len(set(filled)) != len(filled):
            raise ValueError("The initial clues contain duplicate values.")


def candidates(state, index):
    return [v for v in range(1, 10) if v not in {state[j] for j in PEERS[index]}]


def propagate(state):
    """Apply naked singles only: constraint deductions without heuristic ordering."""
    board = list(state)
    while True:
        changed = False
        for i, value in enumerate(board):
            if value:
                continue
            domain = candidates(board, i)
            if not domain:
                return None
            if len(domain) == 1:
                board[i] = domain[0]
                changed = True
        if not changed:
            return tuple(board)


def solved(state):
    try:
        validate(state)
    except ValueError:
        return False
    return 0 not in state


def objective(state):
    """Minimize empty cells plus all-different violations across the 27 units."""
    if len(state) != 81 or any(type(x) is not int or not 0 <= x <= 9 for x in state):
        raise ValueError("Expected 81 integers from 0 to 9.")
    penalty = state.count(0)
    for unit in UNITS:
        values = [state[i] for i in unit if state[i]]
        penalty += len(values) - len(set(values))
    return penalty


def landscape(state):
    validate(state)
    empty = state.count(0)
    product = 1
    for i, v in enumerate(state):
        if not v:
            product *= len(candidates(state, i))
    return {"empty_cells": empty, "raw_assignments": 9 ** empty,
            "initial_domain_product": product,
            "unpruned_tree_nodes": (9 ** (empty + 1) - 1) // 8}


PUZZLES = {
    "easy": (
        "530070000", "600195000", "098000060", "800060003", "400803001",
        "700020006", "060000280", "000419005", "000080079"),
    "medium": (
        "000000907", "000420180", "000705026", "100904000", "050000040",
        "000507009", "920108000", "034059000", "507000000"),
    "hard": (
        "100007090", "030020008", "009600500", "005300900", "010080002",
        "600004000", "300000010", "040000007", "007000300"),
}


def solve(state, method="bfs", propagation=True, max_nodes=200_000,
          max_states=200_000, timeout=20.0):
    validate(state)
    if method not in ("bfs", "dfs"):
        raise ValueError("Method must be bfs or dfs.")
    if max_states < 1:
        raise ValueError("max_states must be positive.")
    stats = Stats()
    budget = Budget(stats, max_nodes, timeout)
    root = propagate(state) if propagation else state
    path, answer = [], None
    if root is None:
        budget.finish()
        return {"status": "unsatisfiable", "solution": None, "path": [],
                "stats": stats.dictionary()}

    def children(board):
        index = board.index(0)  # Fixed row-major selection; no MRV heuristic.
        for value in candidates(board, index):
            child = list(board)
            child[index] = value
            child = propagate(tuple(child)) if propagation else tuple(child)
            if child is not None:
                yield child

    def dfs(board):
        budget.tick()
        path.append(board)
        if 0 not in board:
            return board
        for child in children(board):
            stats.generated += 1
            result = dfs(child)
            if result is not None:
                return result
            stats.backtracks += 1
        path.pop()  # Return to the parent; states are immutable.
        return None

    try:
        if method == "dfs":
            answer = dfs(root)
        else:
            queue = deque([root])
            parent = {root: None}
            stats.max_frontier = 1
            while queue:
                budget.tick()
                board = queue.popleft()  # FIFO order implements BFS.
                if 0 not in board:
                    answer = board
                    cursor = board
                    while cursor is not None:
                        path.append(cursor)
                        cursor = parent[cursor]
                    path.reverse()  # Reconstruct the path through parent links; this is not DFS backtracking.
                    break
                for child in children(board):
                    if child in parent:
                        continue
                    if len(parent) >= max_states:
                        raise SearchLimit("The in-memory state limit was reached.")
                    parent[child] = board
                    queue.append(child)
                    stats.generated += 1
                stats.max_frontier = max(stats.max_frontier, len(queue))
        status = "solved" if answer is not None else "unsatisfiable"
    except SearchLimit:
        status, answer, path = "limit", None, []
    budget.finish()
    # Include the original input if propagation changed the root state.
    if answer is not None and path[0] != state:
        path.insert(0, state)
    return {"status": status, "solution": answer, "path": path,
            "stats": stats.dictionary()}


def show(state):
    for r in range(9):
        if r and r % 3 == 0:
            print("------+-------+------")
        print(" | ".join(" ".join(str(v) if v else "." for v in state[r*9+c:r*9+c+3])
                         for c in (0, 3, 6)))


class SudokuTests(unittest.TestCase):
    def test_three_levels_and_preserved_givens(self):
        for level, rows in PUZZLES.items():
            with self.subTest(level=level):
                start = parse(rows)
                result = solve(start)
                self.assertEqual(result["status"], "solved")
                answer = result["solution"]
                self.assertTrue(solved(answer))
                self.assertEqual(objective(answer), 0)
                self.assertGreater(objective(start), 0)
                self.assertTrue(all(not v or answer[i] == v for i, v in enumerate(start)))
                self.assertEqual(result["path"][0], start)
                self.assertEqual(result["path"][-1], answer)
                for before, after in zip(result["path"], result["path"][1:]):
                    validate(after)
                    self.assertTrue(all(not v or after[i] == v for i, v in enumerate(before)))

    def test_pure_bfs_without_propagation(self):
        answer = solve(parse(PUZZLES["easy"]))["solution"]
        start = (0, 0) + answer[2:]
        result = solve(start, propagation=False)
        self.assertTrue(solved(result["solution"]))
        self.assertEqual(len(result["path"]), 3)
        self.assertEqual(result["stats"]["expanded"], 3)

    def test_dfs_backtracking_alternative(self):
        result = solve(parse(PUZZLES["hard"]), method="dfs")
        self.assertTrue(solved(result["solution"]))
        self.assertGreater(result["stats"]["backtracks"], 0)

    def test_invalid_and_unsatisfiable(self):
        with self.assertRaises(ValueError):
            parse(["110000000"] + ["000000000"] * 8)
        with self.assertRaises(ValueError):
            parse(["000"])
        state = list(parse(PUZZLES["easy"]))
        state[2] = 1  # Locally valid clue that makes the puzzle unsatisfiable.
        self.assertEqual(solve(tuple(state))["status"], "unsatisfiable")

    def test_limits_and_landscape(self):
        state = parse(PUZZLES["hard"])
        self.assertEqual(solve(state, max_nodes=0)["status"], "limit")
        self.assertEqual(solve(state, max_states=1)["status"], "limit")
        self.assertEqual(landscape(state)["raw_assignments"], 9 ** state.count(0))


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        unittest.main(argv=[sys.argv[0]], verbosity=2)
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--level", choices=PUZZLES, default="easy")
        parser.add_argument("--method", choices=("bfs", "dfs"), default="bfs")
        parser.add_argument("--no-propagation", action="store_true")
        parser.add_argument("--max-nodes", type=int, default=200_000)
        parser.add_argument("--max-states", type=int, default=200_000)
        parser.add_argument("--timeout", type=float, default=20)
        args = parser.parse_args()
        start = parse(PUZZLES[args.level])
        result = solve(start, args.method, not args.no_propagation,
                       args.max_nodes, args.max_states, args.timeout)
        print("Level:", args.level, "Method:", args.method, "Status:", result["status"])
        if result["solution"] is not None:
            show(result["solution"])
        print("Statistics:", result["stats"])
        print("Landscape:", landscape(start))

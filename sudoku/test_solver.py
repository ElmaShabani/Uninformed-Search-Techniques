"""Regression tests for Sudoku solutions, search paths, and resource limits."""
import unittest
import model as sudoku
from puzzles import PUZZLES
from solver import solve


class SudokuTests(unittest.TestCase):
    def test_three_levels_and_preserved_givens(self):
        for level, rows in PUZZLES.items():
            with self.subTest(level=level):
                start = sudoku.parse(rows)
                result = solve(start)
                self.assertEqual(result["status"], "solved")
                answer = result["solution"]
                self.assertTrue(sudoku.solved(answer))
                self.assertEqual(sudoku.objective(answer), 0)
                self.assertGreater(sudoku.objective(start), 0)
                self.assertTrue(all(not v or answer[i] == v for i, v in enumerate(start)))
                self.assertEqual(result["path"][0], start)
                self.assertEqual(result["path"][-1], answer)
                for before, after in zip(result["path"], result["path"][1:]):
                    sudoku.validate(after)
                    self.assertTrue(all(not v or after[i] == v for i, v in enumerate(before)))

    def test_pure_bfs_without_propagation(self):
        answer = solve(sudoku.parse(PUZZLES["easy"]))["solution"]
        start = (0, 0) + answer[2:]
        result = solve(start, propagation=False)
        self.assertTrue(sudoku.solved(result["solution"]))
        self.assertEqual(len(result["path"]), 3)
        self.assertEqual(result["stats"]["expanded"], 3)

    def test_dfs_backtracking_alternative(self):
        result = solve(sudoku.parse(PUZZLES["hard"]), method="dfs")
        self.assertTrue(sudoku.solved(result["solution"]))
        self.assertGreater(result["stats"]["backtracks"], 0)

    def test_invalid_and_unsatisfiable(self):
        with self.assertRaises(ValueError):
            sudoku.parse(["110000000"] + ["000000000"] * 8)
        with self.assertRaises(ValueError):
            sudoku.parse(["000"])
        state = list(sudoku.parse(PUZZLES["easy"]))
        state[2] = 1  # Locally valid clue that makes the puzzle unsatisfiable.
        self.assertEqual(solve(tuple(state))["status"], "unsatisfiable")

    def test_limits_and_landscape(self):
        state = sudoku.parse(PUZZLES["hard"])
        self.assertEqual(solve(state, max_nodes=0)["status"], "limit")
        self.assertEqual(solve(state, max_states=1)["status"], "limit")
        self.assertEqual(sudoku.landscape(state)["raw_assignments"], 9 ** state.count(0))


if __name__ == "__main__":
    unittest.main()

"""Sudoku using FIFO breadth-first search and optional DFS backtracking.

Run: python3 sudoku/solver.py --level easy
BFS reconstructs its path through parent links. Recursive backtracking is
provided separately through --method dfs. Optional naked-single propagation
applies constraint deductions without heuristic ordering of search choices.
"""
import argparse
from collections import deque

from model import candidates, landscape, parse, propagate, validate
from puzzles import PUZZLES
from search_utils import Stats, Budget, SearchLimit


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


if __name__ == "__main__":
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

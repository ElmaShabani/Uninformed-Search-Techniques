"""Latin Square using iterative deepening DFS and backtracking.

Run: python3 latin_square/solver.py 5
Depth limits increase from 0 through n*n. A failed assignment is undone before
trying the next value. The first row and column are fixed to break symmetry.
"""
import argparse
from model import landscape
from search_utils import Stats, Budget, SearchLimit


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


if __name__ == "__main__":
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

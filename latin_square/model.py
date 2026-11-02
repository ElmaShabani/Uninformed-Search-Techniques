"""Latin Square constraint model.

Each of the n*n cells is a variable with domain 1..n; 0 denotes an empty cell.
Every row and column must contain each domain value exactly once.
States are lists of n rows. The objective counts empty cells and duplicates.
Landscape counts ignore constraints and are not counts of valid Latin squares.
"""

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


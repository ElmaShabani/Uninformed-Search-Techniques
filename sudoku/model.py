"""Sudoku constraint model.

Variables are the 81 cells; empty cells have domains drawn from 1..9.
A tuple of 81 integers represents a state, with 0 marking an empty cell.
Rows, columns, and 3x3 boxes must each contain distinct nonzero values.
The objective counts empty cells and duplicate values in all 27 units.
Landscape counts are relaxed search space sizes, not valid solution counts.
"""

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


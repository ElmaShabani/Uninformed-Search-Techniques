"""Initial model for the Social Golfers problem.

The variable x[week, player] assigns a player to a group for that week.
The domain is {0, ..., g-1}; players are numbered from 0 to g*p-1.
Each group contains p players, and no pair may meet more than once.
The schedule is a list of weeks, each containing g lists of players.
"""

from itertools import combinations
from math import factorial


def upper_bound(g, p):
    """Each player meets p-1 new players per week out of g*p-1 other players."""
    if g < 1 or p < 2:
        raise ValueError("Kërkohet g >= 1 dhe p >= 2.")
    return (g * p - 1) // (p - 1)


def landscape(g, p, w):
    """Search space sizes before checking for repeated pairs.

    Groups are treated as unordered when counting weekly partitions.
    These sizes do not count schedules that satisfy all constraints.
    """
    bound = upper_bound(g, p)
    if w < 1:
        raise ValueError("Numri i javëve duhet të jetë pozitiv.")
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


if __name__ == "__main__":
    first_week = [[list(range(k * 4, (k + 1) * 4)) for k in range(8)]]
    print("Social Golfers: 32 lojtarë, 8 grupe me nga 4.")
    print("Kufiri i sipërm i javëve:", upper_bound(8, 4))
    print("Java fillestare është valide:", valid(first_week, 8, 4, 1))
    print("Takime të përsëritura:", objective(first_week))
    print("Landscape për 3 javë:")
    for name, value in landscape(8, 4, 3).items():
        print(f"  {name}: {value}")

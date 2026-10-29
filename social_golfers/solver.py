"""Social Golfers me DFS dhe Backtracking.

Ekzekutimi: python3 social_golfers/solver.py --groups 8 --size 4 --weeks 3
Kufiri teorik i javëve nuk garanton se DFS e gjen një orar brenda kohës.
"""
import argparse
from itertools import combinations

from model import landscape, upper_bound
from search_utils import Budget, Stats, SearchLimit


def solve(g=8, p=4, w=3, max_nodes=200_000, timeout=20.0):
    bound = upper_bound(g, p)
    if w < 1:
        raise ValueError("w duhet pozitiv.")
    stats = Stats()
    budget = Budget(stats, max_nodes, timeout)
    if w > bound:
        budget.finish()
        return {"status": "unsatisfiable", "schedule": None,
                "reason": "Tejkalohet kufiri teorik i javëve.", "stats": stats.dictionary()}
    n = g * p
    # Riemërtimi i lojtarëve e bën javën e parë fikse pa humbur zgjidhje.
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
            # Undo i plotë: grupi dhe çiftet kthehen në gjendjen e mëparshme.
            group.pop()
            seen.difference_update(pairs)
            stats.backtracks += 1
            # Grupet bosh janë simetrike: provohet vetëm i pari.
            if was_empty:
                break
        return False

    try:
        found = next_week()
        status, reason = ("solved", "U gjet orar valid.") if found else (
            "unsatisfiable", "U shterua hapësira e kërkimit.")
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
        print(f"Java {i}: " + " | ".join(",".join(map(str, group)) for group in week))
    if "stats" in result:
        print(result["reason"], result["stats"])
    print("Landscape:", landscape(args.groups, args.size, args.weeks))


if __name__ == "__main__":
    main()

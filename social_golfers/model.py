"""Modeli fillestar për Social Golfers.

Variabla x[java, lojtari] përcakton grupin e lojtarit atë javë.
Domain-i është {0, ..., g-1}; lojtarët numërohen nga 0 në g*p-1.
Çdo grup ka p lojtarë dhe asnjë çift nuk lejohet të përsëritet.
Orari ruhet si listë javësh, secila me g lista lojtarësh.
"""

from itertools import combinations
from math import factorial


def upper_bound(g, p):
    """Çdo lojtar takon p-1 lojtarë të rinj në javë, nga g*p-1 gjithsej."""
    if g < 1 or p < 2:
        raise ValueError("Kërkohet g >= 1 dhe p >= 2.")
    return (g * p - 1) // (p - 1)


def landscape(g, p, w):
    """Madhësitë e hapësirës para kontrollit të çifteve të përsëritura.

    Grupet trajtohen pa renditje në numërimin e ndarjeve javore.
    Këto madhësi nuk janë numri i orareve që e zgjidhin problemin.
    """
    bound = upper_bound(g, p)
    if w < 1:
        raise ValueError("Numri i javëve duhet të jetë pozitiv.")
    n = g * p
    # Hiq renditjet brenda çdo grupi dhe renditjet e vetë grupeve.
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
    """Minimizo takimet e përsëritura; një orar i vlefshëm ka vlerën 0."""
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
    """Kontrollo javët, madhësitë, pjesëmarrjen dhe çiftet e përsëritura."""
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

"""Shared search utilities. Requires only the Python 3.10+ standard library."""
from dataclasses import dataclass, asdict
from time import perf_counter


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
            raise SearchLimit("U arrit kufiri i nyjave; rezultati mbetet i panjohur.")
        if self.timeout is not None and perf_counter() - self.start >= self.timeout:
            raise SearchLimit("U arrit kufiri kohor; rezultati mbetet i panjohur.")
        self.stats.expanded += 1

    def finish(self):
        self.stats.seconds = perf_counter() - self.start

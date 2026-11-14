"""Uniform-cost search on a Grid, written as an event generator.

UCS always expands the frontier cell with the lowest accumulated cost g(n).
It is A* with h(n) = 0, so it shares its implementation with A*
(see best_first). Event meaning is documented once, in EventType.
"""

from collections.abc import Iterator

from ai_intelligence_lab.algorithms.search.best_first import best_first
from ai_intelligence_lab.core.events import AlgorithmEvent
from ai_intelligence_lab.environments.grid import Grid, Position


def _no_estimate(cell: Position) -> float:
    return 0.0


def ucs(grid: Grid) -> Iterator[AlgorithmEvent]:
    return best_first(grid, _no_estimate)

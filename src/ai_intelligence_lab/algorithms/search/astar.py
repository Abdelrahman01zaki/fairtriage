"""A* search on a Grid, written as an event generator.

A* expands the frontier cell with the lowest f(n) = g(n) + h(n), where
g(n) is the cost paid so far and h(n) estimates the cost still to go.
The search itself lives in best_first, shared with UCS.

h(n) is the Manhattan distance scaled by the cheapest step cost in the
grid. Scaling keeps h from overestimating when some cells cost less
than DEFAULT_COST, so the path found is always a cheapest one.

The ``cost`` field of every event is g(n), never f(n).
"""

from collections.abc import Iterator

from ai_intelligence_lab.algorithms.search.best_first import best_first
from ai_intelligence_lab.algorithms.search.heuristics import manhattan
from ai_intelligence_lab.core.events import AlgorithmEvent
from ai_intelligence_lab.environments.grid import DEFAULT_COST, Grid, Position


def astar(grid: Grid) -> Iterator[AlgorithmEvent]:
    goal = grid.goal

    # Cheapest possible step: a lower bound, so h never overestimates.
    min_step = min([DEFAULT_COST, *grid.weights.values()])

    def h(cell: Position) -> float:
        return manhattan(cell, goal) * min_step

    return best_first(grid, h)

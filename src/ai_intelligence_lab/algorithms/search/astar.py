"""A* search on a Grid, written as an event generator.

A* expands the frontier cell with the lowest f(n) = g(n) + h(n), where
g(n) is the cost paid so far and h(n) estimates the cost still to go.

h(n) is the Manhattan distance scaled by the cheapest step cost in the
grid. Scaling keeps h from overestimating when some cells cost less
than DEFAULT_COST, so the path found is always a cheapest one.

Events use the same vocabulary as UCS. The ``cost`` field is always
g(n), the real cost paid, never f(n).
"""

import heapq
from collections.abc import Iterator
from itertools import count

from ai_intelligence_lab.algorithms.search.heuristics import manhattan
from ai_intelligence_lab.algorithms.search.paths import build_path
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import DEFAULT_COST, Grid, Position


def astar(grid: Grid) -> Iterator[AlgorithmEvent]:
    start, goal = grid.start, grid.goal

    # Cheapest possible step: a lower bound, so h never overestimates.
    min_step = min([DEFAULT_COST, *grid.weights.values()])

    def h(cell: Position) -> float:
        return manhattan(cell, goal) * min_step

    # Breaks ties between equal f values in discovery order (FIFO).
    tie_breaker = count()

    best_known_cost: dict[Position, float] = {start: 0.0}
    parents: dict[Position, Position | None] = {}
    # (f, tie, g, cell, parent)
    frontier: list[tuple[float, int, float, Position, Position | None]] = [
        (h(start), next(tie_breaker), 0.0, start, None)
    ]

    yield AlgorithmEvent(EventType.STARTED, node=start, cost=0.0)

    while frontier:
        _, _, cost_so_far, current, parent = heapq.heappop(frontier)

        if current in parents:
            continue  # a stale, more expensive copy of an expanded cell

        parents[current] = parent
        yield AlgorithmEvent(EventType.NODE_EXPANDED, node=current, cost=cost_so_far)

        if current == goal:
            yield AlgorithmEvent(
                EventType.PATH_FOUND,
                node=current,
                path=build_path(parents, current),
                cost=cost_so_far,
            )
            break

        for neighbor in grid.neighbors(current):
            if neighbor in parents:
                continue  # already expanded with its final cost

            new_cost = cost_so_far + grid.cost(neighbor)
            known_cost = best_known_cost.get(neighbor)

            if known_cost is not None and new_cost >= known_cost:
                continue  # we already have an equal-or-cheaper route

            event_kind = (
                EventType.NODE_DISCOVERED
                if known_cost is None
                else EventType.NODE_UPDATED
            )
            best_known_cost[neighbor] = new_cost
            heapq.heappush(
                frontier,
                (
                    new_cost + h(neighbor),
                    next(tie_breaker),
                    new_cost,
                    neighbor,
                    current,
                ),
            )
            yield AlgorithmEvent(
                event_kind, node=neighbor, parent=current, cost=new_cost
            )

    yield AlgorithmEvent(EventType.COMPLETED)

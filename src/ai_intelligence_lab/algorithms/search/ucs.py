"""Uniform-cost search on a Grid, written as an event generator.

UCS always expands the frontier cell with the lowest accumulated cost
g(n), using a binary heap as a priority queue. It is a special case of
A* with h(n) = 0.

Event vocabulary (extends the one shared with BFS/DFS):
    NODE_DISCOVERED(node, parent, cost)  first time the cell is reached,
                                          with the cost of that route
    NODE_UPDATED(node, parent, cost)     a cheaper route to an
                                          already-discovered, not-yet-
                                          expanded cell was found
    NODE_EXPANDED(node, cost)            the cell was popped from the
                                          frontier with its final g(n)

A cell's parent and cost are only final once it is EXPANDED. Until then,
a cheaper route may still replace them, which is exactly what
NODE_UPDATED reports.
"""

import heapq
from collections.abc import Iterator
from itertools import count

from ai_intelligence_lab.algorithms.search.paths import build_path
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid, Position


def ucs(grid: Grid) -> Iterator[AlgorithmEvent]:
    start, goal = grid.start, grid.goal

    # Tie-breaker so heapq never has to compare two Position tuples with
    # equal cost (which would raise if they aren't orderable).
    tie_breaker = count()

    best_known_cost: dict[Position, float] = {start: 0.0}
    parents: dict[Position, Position | None] = {}
    frontier: list[tuple[float, int, Position, Position | None]] = [
        (0.0, next(tie_breaker), start, None)
    ]

    yield AlgorithmEvent(EventType.STARTED, node=start, cost=0.0)

    while frontier:
        cost_so_far, _, current, parent = heapq.heappop(frontier)

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
                continue  # already expanded with its final, cheapest cost

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
            heapq.heappush(frontier, (new_cost, next(tie_breaker), neighbor, current))
            yield AlgorithmEvent(
                event_kind, node=neighbor, parent=current, cost=new_cost
            )

    yield AlgorithmEvent(EventType.COMPLETED)

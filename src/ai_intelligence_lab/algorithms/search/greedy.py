"""Greedy best-first search on a Grid, written as an event generator.

Greedy always expands the frontier cell that looks closest to the goal,
using the heuristic h(n) only. It ignores the cost already paid, so it
is fast but NOT guaranteed to find the cheapest (or shortest) path.

Every cell is discovered once and its parent never changes, so this
algorithm never emits NODE_UPDATED. Only PATH_FOUND carries a cost: the
real cost of the route that was found, so it can be compared with UCS.
"""

import heapq
from collections.abc import Iterator
from itertools import count

from ai_intelligence_lab.algorithms.search.heuristics import manhattan
from ai_intelligence_lab.algorithms.search.paths import build_path
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid, Position


def greedy(grid: Grid) -> Iterator[AlgorithmEvent]:
    start, goal = grid.start, grid.goal

    # Breaks ties between equal h values in discovery order (FIFO).
    tie_breaker = count()

    parents: dict[Position, Position | None] = {start: None}
    frontier: list[tuple[int, int, Position]] = [
        (manhattan(start, goal), next(tie_breaker), start)
    ]

    yield AlgorithmEvent(EventType.STARTED, node=start)

    while frontier:
        _, _, current = heapq.heappop(frontier)
        yield AlgorithmEvent(EventType.NODE_EXPANDED, node=current)

        if current == goal:
            path = build_path(parents, current)
            route_cost = grid.path_cost(path)
            yield AlgorithmEvent(
                EventType.PATH_FOUND,
                node=current,
                path=path,
                cost=route_cost,
            )
            break

        for neighbor in grid.neighbors(current):
            if neighbor in parents:
                continue  # already discovered; greedy never revises it

            parents[neighbor] = current
            heapq.heappush(
                frontier,
                (manhattan(neighbor, goal), next(tie_breaker), neighbor),
            )
            yield AlgorithmEvent(
                EventType.NODE_DISCOVERED, node=neighbor, parent=current
            )

    yield AlgorithmEvent(EventType.COMPLETED)

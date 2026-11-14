"""Best-first search core shared by UCS and A*.

Both expand the frontier cell with the lowest f(n) = g(n) + h(n), where g(n)
is the cost paid so far and h(n) estimates the cost still to go. UCS is the
special case h(n) = 0, so the two algorithms share this one implementation.

Event meaning is documented once, in EventType. Here the ``cost`` field is
always g(n), the real cost paid, never f(n). A cell's parent and cost are only
final once it is EXPANDED; until then a cheaper route may replace them, which
is what NODE_UPDATED reports.
"""

import heapq
from collections.abc import Callable, Iterator
from itertools import count

from ai_intelligence_lab.algorithms.search.paths import build_path
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid, Position

Heuristic = Callable[[Position], float]


def best_first(grid: Grid, h: Heuristic) -> Iterator[AlgorithmEvent]:
    start, goal = grid.start, grid.goal

    # Equal f values leave the heap in the order they entered (FIFO). That
    # keeps the event order identical on every run, and the heap never has
    # to compare two cells or parents.
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

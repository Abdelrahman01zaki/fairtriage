"""Best-first search core shared by UCS and A*.

Both expand the frontier node with the lowest f(n) = g(n) + h(n), where g(n)
is the cost paid so far and h(n) estimates the cost still to go. UCS is the
special case h(n) = 0, so the two algorithms share this one implementation.

It works on any SearchSpace, not only on a Grid.

Event meaning is documented once, in EventType. Here the ``cost`` field is
always g(n), the real cost paid, never f(n). A node's parent and cost are only
final once it is EXPANDED; until then a cheaper route may replace them, which
is what NODE_UPDATED reports.
"""

import heapq
from collections.abc import Callable, Iterator
from itertools import count

from ai_intelligence_lab.algorithms.search.paths import build_path
from ai_intelligence_lab.algorithms.search.space import Node, SearchSpace
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType

Heuristic = Callable[[Node], float]


def best_first(
    space: SearchSpace[Node], h: Heuristic[Node]
) -> Iterator[AlgorithmEvent]:
    start, goal = space.start, space.goal

    # Equal f values leave the heap in the order they entered (FIFO). That
    # keeps the event order identical on every run, and the heap never has
    # to compare two nodes or parents.
    tie_breaker = count()

    best_known_cost: dict[Node, float] = {start: 0.0}
    parents: dict[Node, Node | None] = {}
    # (f, tie, g, node, parent)
    frontier: list[tuple[float, int, float, Node, Node | None]] = [
        (h(start), next(tie_breaker), 0.0, start, None)
    ]

    yield AlgorithmEvent(EventType.STARTED, node=start, cost=0.0)

    while frontier:
        _, _, cost_so_far, current, parent = heapq.heappop(frontier)

        if current in parents:
            continue  # a stale, more expensive copy of an expanded node

        parents[current] = parent
        yield AlgorithmEvent(EventType.NODE_EXPANDED, node=current, cost=cost_so_far)

        if current == goal:
            path = build_path(parents, current)
            yield AlgorithmEvent(
                EventType.PATH_FOUND,
                node=current,
                path=path,
                cost=cost_so_far,
            )
            break

        for neighbor in space.neighbors(current):
            if neighbor in parents:
                continue  # already expanded with its final cost

            new_cost = cost_so_far + space.step_cost(current, neighbor)
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

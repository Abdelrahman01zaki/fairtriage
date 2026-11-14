"""Breadth-first search on a Grid, written as an event generator.

The generator never draws anything and never measures anything. It only
reports what happened, one event at a time. Whoever consumes the events
(console, Pygame, benchmark, test) decides what to do with them.

Event order for one run:
    STARTED(node=start)
    then, for every cell taken from the queue:
        NODE_EXPANDED(node)
        PATH_FOUND(node, path)        only if the cell is the goal
        NODE_DISCOVERED(node, parent) for each new neighbour
    COMPLETED                         always the last event

The start cell is known from STARTED, so it gets no NODE_DISCOVERED.
"""

from collections import deque
from collections.abc import Iterator

from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid, Position


def bfs(grid: Grid) -> Iterator[AlgorithmEvent]:
    start, goal = grid.start, grid.goal

    # parents also acts as the "already discovered" set.
    parents: dict[Position, Position | None] = {start: None}
    frontier: deque[Position] = deque([start])

    yield AlgorithmEvent(EventType.STARTED, node=start)

    while frontier:
        current = frontier.popleft()
        yield AlgorithmEvent(EventType.NODE_EXPANDED, node=current)

        if current == goal:
            yield AlgorithmEvent(
                EventType.PATH_FOUND,
                node=current,
                path=_build_path(parents, current),
            )
            break

        for neighbor in grid.neighbors(current):
            if neighbor in parents:
                continue

            parents[neighbor] = current
            frontier.append(neighbor)

            yield AlgorithmEvent(
                EventType.NODE_DISCOVERED,
                node=neighbor,
                parent=current,
            )

    yield AlgorithmEvent(EventType.COMPLETED)


def _build_path(
    parents: dict[Position, Position | None], goal: Position
) -> tuple[Position, ...]:
    """Walk the parent links back from the goal, then reverse."""
    path: list[Position] = []
    node: Position | None = goal

    while node is not None:
        path.append(node)
        node = parents[node]

    path.reverse()
    return tuple(path)

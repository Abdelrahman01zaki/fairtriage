"""Depth-first search on a Grid, written as an event generator.

Same event vocabulary and same meaning as every other search algorithm
(see EventType): DISCOVERED the first time a cell enters the frontier (a
stack here), UPDATED when it is pushed again with a different parent, and
EXPANDED when it is popped.

Two things differ from BFS, and both come from DFS itself:

* The frontier is a stack, so the newest cell is expanded first.
* A cell is marked when it is EXPANDED, not when it is discovered. The same
  cell can therefore be pushed more than once, through different parents,
  before it is expanded. The most recent push is popped first, so it decides
  the tree parent. Older copies are skipped silently when they surface.
"""

from collections.abc import Iterator

from ai_intelligence_lab.algorithms.search.paths import build_path
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid, Position


def dfs(grid: Grid) -> Iterator[AlgorithmEvent]:
    start, goal = grid.start, grid.goal

    # Filled when a cell is expanded; it doubles as the "expanded" set.
    parents: dict[Position, Position | None] = {}
    # Every cell that has entered the frontier so far.
    seen: set[Position] = {start}
    stack: list[tuple[Position, Position | None]] = [(start, None)]

    yield AlgorithmEvent(EventType.STARTED, node=start)

    while stack:
        current, parent = stack.pop()
        if current in parents:
            continue  # an older copy of a cell that was already expanded

        parents[current] = parent
        yield AlgorithmEvent(EventType.NODE_EXPANDED, node=current)

        if current == goal:
            path = build_path(parents, current)
            yield AlgorithmEvent(
                EventType.PATH_FOUND,
                node=current,
                path=path,
            )
            break

        fresh = [n for n in grid.neighbors(current) if n not in parents]
        for neighbor in fresh:
            kind = (
                EventType.NODE_UPDATED
                if neighbor in seen
                else EventType.NODE_DISCOVERED
            )
            seen.add(neighbor)
            yield AlgorithmEvent(kind, node=neighbor, parent=current)

        # Pushed in reverse, so the first neighbour stays first to be popped.
        stack.extend((neighbor, current) for neighbor in reversed(fresh))

    yield AlgorithmEvent(EventType.COMPLETED)

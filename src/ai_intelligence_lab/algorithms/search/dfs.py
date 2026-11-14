"""Depth-first search on a Grid, written as an event generator.

Same event vocabulary and same meaning as BFS:
    NODE_DISCOVERED(node, parent)  the cell was added to the frontier (a stack)
    NODE_EXPANDED(node)            the cell was taken from the frontier

Two things differ from BFS, and both come from DFS itself:

* The frontier is a stack, so the newest cell is expanded first.
* A cell is marked when it is EXPANDED, not when it is discovered. The same
  cell can therefore be discovered more than once, through different
  parents, before it is expanded. The most recent push is popped first, so
  it decides the tree parent. Older copies are skipped silently when they
  surface.
"""

from collections.abc import Iterator

from ai_intelligence_lab.algorithms.search.paths import build_path
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid, Position


def dfs(grid: Grid) -> Iterator[AlgorithmEvent]:
    start, goal = grid.start, grid.goal

    # Filled when a cell is expanded; it doubles as the "expanded" set.
    parents: dict[Position, Position | None] = {}
    stack: list[tuple[Position, Position | None]] = [(start, None)]

    yield AlgorithmEvent(EventType.STARTED, node=start)

    while stack:
        current, parent = stack.pop()
        if current in parents:
            continue  # an older copy of a cell that was already expanded

        parents[current] = parent
        yield AlgorithmEvent(EventType.NODE_EXPANDED, node=current)

        if current == goal:
            yield AlgorithmEvent(
                EventType.PATH_FOUND,
                node=current,
                path=build_path(parents, current),
            )
            break

        fresh = [n for n in grid.neighbors(current) if n not in parents]
        for neighbor in fresh:
            yield AlgorithmEvent(
                EventType.NODE_DISCOVERED,
                node=neighbor,
                parent=current,
            )

        # Pushed in reverse, so the first neighbour stays first to be popped.
        stack.extend((neighbor, current) for neighbor in reversed(fresh))

    yield AlgorithmEvent(EventType.COMPLETED)

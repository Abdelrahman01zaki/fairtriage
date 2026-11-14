"""Metrics consumer: turns one event stream into a summary of the run.

Like the console printer, this is an event consumer. The algorithms know
nothing about it. Every algorithm is measured the same way, so BFS, DFS,
UCS, Greedy and A* can be compared fairly.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from time import perf_counter
from typing import cast

from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid, Position


@dataclass(frozen=True, slots=True)
class SearchMetrics:
    """What happened during one run, counted from its events."""

    events: int
    expanded: int
    discovered: int
    updated: int
    path: tuple[Position, ...] | None
    path_cost: float | None
    seconds: float

    @property
    def found(self) -> bool:
        return self.path is not None


def measure(grid: Grid, events: Iterable[AlgorithmEvent]) -> SearchMetrics:
    """Consume ``events`` and summarize the run.

    ``seconds`` covers the whole consumption. Generators are lazy, so it
    includes the time the algorithm itself spent producing the events.

    ``path_cost`` is always computed from the grid, never read from an
    event. That way BFS and DFS, which emit no cost, are comparable with
    UCS and A*.
    """
    total = expanded = discovered = updated = 0
    path: tuple[Position, ...] | None = None

    started = perf_counter()
    for event in events:
        total += 1
        if event.kind is EventType.NODE_EXPANDED:
            expanded += 1
        elif event.kind is EventType.NODE_DISCOVERED:
            discovered += 1
        elif event.kind is EventType.NODE_UPDATED:
            updated += 1
        elif event.kind is EventType.PATH_FOUND:
            path = cast("tuple[Position, ...] | None", event.path)
    seconds = perf_counter() - started

    path_cost = (
        None if path is None else sum((grid.cost(c) for c in path[1:]), 0.0)
    )
    return SearchMetrics(
        events=total,
        expanded=expanded,
        discovered=discovered,
        updated=updated,
        path=path,
        path_cost=path_cost,
        seconds=seconds,
    )

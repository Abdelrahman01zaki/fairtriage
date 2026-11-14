"""Helpers shared by the search algorithms."""

from collections.abc import Mapping

from ai_intelligence_lab.environments.grid import Position


def build_path(
    parents: Mapping[Position, Position | None], goal: Position
) -> tuple[Position, ...]:
    """Walk the parent links back from the goal, then reverse."""
    path: list[Position] = []
    node: Position | None = goal

    while node is not None:
        path.append(node)
        node = parents[node]

    path.reverse()
    return tuple(path)

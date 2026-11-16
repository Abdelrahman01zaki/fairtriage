"""Helpers shared by the search algorithms."""

from collections.abc import Mapping
from typing import TypeVar

T = TypeVar("T")


def build_path(parents: Mapping[T, T | None], goal: T) -> tuple[T, ...]:
    """Walk the parent links back from the goal, then reverse."""
    path: list[T] = []
    current: T | None = goal

    while current is not None:
        path.append(current)
        current = parents[current]

    path.reverse()
    return tuple(path)

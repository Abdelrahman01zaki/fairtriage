"""Core event model shared by all algorithm families."""

from collections.abc import Hashable
from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    """What happened at one step of an algorithm run."""

    STARTED = auto()
    NODE_DISCOVERED = auto()
    NODE_UPDATED = auto()
    NODE_EXPANDED = auto()
    PATH_FOUND = auto()
    COMPLETED = auto()


@dataclass(frozen=True, slots=True)
class AlgorithmEvent:
    """One lightweight, immutable record of something that happened."""

    kind: EventType
    node: Hashable | None = None
    parent: Hashable | None = None
    path: tuple[Hashable, ...] | None = None
    cost: float | None = None

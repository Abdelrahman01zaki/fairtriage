"""Core event model shared by all algorithm families."""

from collections.abc import Hashable
from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    """What happened at one step of an algorithm run.

    The meaning is the same for every search algorithm:

    STARTED          the run began at the start node
    NODE_DISCOVERED  a node entered the frontier for the first time
    NODE_UPDATED     a node already on the frontier got a new tentative parent
                     (a cheaper one in UCS and A*, a more recent one in DFS)
    NODE_EXPANDED    a node left the frontier and its neighbours were examined
    PATH_FOUND       a path to the goal was found
    COMPLETED        the run ended
    """

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

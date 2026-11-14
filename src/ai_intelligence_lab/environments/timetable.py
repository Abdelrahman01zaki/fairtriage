"""University timetable world: lectures, rooms, periods and availability.

This module is plain data with validation, like Grid. It knows nothing about
how a timetable gets solved; the CSP formulation lives in algorithms/csp.
"""

from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class Period:
    """One teaching slot, such as the first slot on Saturday."""

    day: str
    slot: int

    def __post_init__(self) -> None:
        if not self.day:
            raise ValueError("a period needs a day")
        if self.slot <= 0:
            raise ValueError("slot numbers start at 1")

    def __str__(self) -> str:
        return f"{self.day} {self.slot}"


@dataclass(frozen=True, slots=True)
class Room:
    name: str
    capacity: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a room needs a name")
        if self.capacity <= 0:
            raise ValueError(f"room {self.name!r} needs a positive capacity")


@dataclass(frozen=True, slots=True)
class Lecture:
    """One weekly lecture that has to be given exactly once.

    ``curricula`` are the student groups attending it. Two lectures that share
    a curriculum cannot run at the same time.
    """

    id: str
    teacher: str
    curricula: frozenset[str]
    students: int

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("a lecture needs an id")
        if not self.teacher:
            raise ValueError(f"lecture {self.id!r} needs a teacher")
        if self.students <= 0:
            raise ValueError(f"lecture {self.id!r} needs a positive student count")
        if isinstance(self.curricula, str):
            raise ValueError(f"lecture {self.id!r}: curricula must be a collection")
        object.__setattr__(self, "curricula", frozenset(self.curricula))


@dataclass(frozen=True, slots=True)
class Timetable:
    """Everything needed to ask: can these lectures be scheduled?

    ``unavailable`` maps a teacher to the periods they cannot teach in.
    """

    lectures: tuple[Lecture, ...]
    rooms: tuple[Room, ...]
    periods: tuple[Period, ...]
    unavailable: Mapping[str, frozenset[Period]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        lectures = tuple(self.lectures)
        rooms = tuple(self.rooms)
        periods = tuple(self.periods)
        if not lectures:
            raise ValueError("a timetable needs at least one lecture")
        if not rooms:
            raise ValueError("a timetable needs at least one room")
        if not periods:
            raise ValueError("a timetable needs at least one period")
        _require_unique("lecture id", (lecture.id for lecture in lectures))
        _require_unique("room name", (room.name for room in rooms))
        _require_unique("period", periods)

        teachers = {lecture.teacher for lecture in lectures}
        known_periods = set(periods)
        unavailable: dict[str, frozenset[Period]] = {}
        for teacher, blocked in self.unavailable.items():
            if teacher not in teachers:
                raise ValueError(
                    f"unavailability given for unknown teacher {teacher!r}"
                )
            blocked_periods = frozenset(blocked)
            if not blocked_periods <= known_periods:
                raise ValueError(
                    f"teacher {teacher!r} is unavailable at a period "
                    "that is not in the timetable"
                )
            unavailable[teacher] = blocked_periods

        # Freeze private copies, as Grid does.
        object.__setattr__(self, "lectures", lectures)
        object.__setattr__(self, "rooms", rooms)
        object.__setattr__(self, "periods", periods)
        object.__setattr__(self, "unavailable", MappingProxyType(unavailable))


def _require_unique(what: str, items: Iterable[Hashable]) -> None:
    seen: set[Hashable] = set()
    for item in items:
        if item in seen:
            raise ValueError(f"duplicate {what}: {item!r}")
        seen.add(item)

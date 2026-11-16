"""Road network: junctions with positions, and roads with travel times.

Junction ids are the names used by ``Hospital.location``, ``Ambulance.base``
and ``Incident.location``. Times are minutes. Positions are only used to
estimate straight-line distance, never to decide how long a road takes.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class Junction:
    id: str
    x: float
    y: float

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("a junction needs an id")
        if not (math.isfinite(self.x) and math.isfinite(self.y)):
            raise ValueError(f"junction {self.id!r} needs a finite position")


@dataclass(frozen=True, slots=True)
class Road:
    """A road between two junctions, two-way unless ``two_way`` is False."""

    source: str
    target: str
    minutes: float
    two_way: bool = True

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise ValueError("a road needs a source and a target")
        if self.source == self.target:
            raise ValueError(f"road at {self.source!r} cannot loop back to itself")
        if not math.isfinite(self.minutes) or self.minutes <= 0:
            raise ValueError(
                f"road {self.source!r}-{self.target!r} needs a positive, "
                "finite travel time"
            )


@dataclass(frozen=True, slots=True)
class RoadNetwork:
    junctions: tuple[Junction, ...]
    roads: tuple[Road, ...]
    _next: Mapping[str, Mapping[str, float]] = field(
        init=False, repr=False, compare=False
    )
    _position: Mapping[str, tuple[float, float]] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        junctions = tuple(self.junctions)
        roads = tuple(self.roads)
        if not junctions:
            raise ValueError("a road network needs at least one junction")

        ids = [junction.id for junction in junctions]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate junction id in the road network")

        known = set(ids)
        outgoing: dict[str, dict[str, float]] = {name: {} for name in ids}
        for road in roads:
            for end in (road.source, road.target):
                if end not in known:
                    raise ValueError(
                        f"road {road.source!r}-{road.target!r} "
                        f"uses unknown junction {end!r}"
                    )
            moves = [(road.source, road.target)]
            if road.two_way:
                moves.append((road.target, road.source))
            for source, target in moves:
                if target in outgoing[source]:
                    raise ValueError(
                        f"more than one road from {source!r} to {target!r}"
                    )
                outgoing[source][target] = road.minutes

        # Freeze private copies, as Grid does.
        object.__setattr__(self, "junctions", junctions)
        object.__setattr__(self, "roads", roads)
        object.__setattr__(
            self,
            "_next",
            MappingProxyType(
                {name: MappingProxyType(moves) for name, moves in outgoing.items()}
            ),
        )
        object.__setattr__(
            self,
            "_position",
            MappingProxyType({j.id: (j.x, j.y) for j in junctions}),
        )

    def neighbors(self, junction: str) -> tuple[str, ...]:
        """Junctions reachable in one move, in the order the roads were given."""
        if junction not in self._next:
            raise ValueError(f"unknown junction {junction!r}")
        return tuple(self._next[junction])

    def travel_minutes(self, source: str, target: str) -> float:
        """Minutes to drive the road from ``source`` to ``target``."""
        try:
            return self._next[source][target]
        except KeyError:
            raise ValueError(f"no road from {source!r} to {target!r}") from None

    def distance(self, first: str, second: str) -> float:
        """Straight-line distance between two junctions."""
        for name in (first, second):
            if name not in self._position:
                raise ValueError(f"unknown junction {name!r}")
        (x1, y1), (x2, y2) = self._position[first], self._position[second]
        return math.hypot(x2 - x1, y2 - y1)

    def without_road(self, first: str, second: str) -> "RoadNetwork":
        """A new network with every road between the two junctions removed.

        The original network is not changed. Use it to model a closed road.
        """
        kept = tuple(r for r in self.roads if {r.source, r.target} != {first, second})
        if len(kept) == len(self.roads):
            raise ValueError(f"no road between {first!r} and {second!r}")
        return RoadNetwork(self.junctions, kept)

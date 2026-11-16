"""Fastest route between two junctions of a road network.

The search is A* on the shared best-first core. The estimate of the time still
to go is the straight-line distance divided by the highest speed found on any
road of the network. No real road can beat that speed, so the estimate never
overshoots and the route found is always a fastest one.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import cast

from ai_intelligence_lab.algorithms.search.best_first import best_first
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.road_network import RoadNetwork


@dataclass(frozen=True, slots=True)
class Route:
    """A route: the junctions in driving order and the minutes it takes."""

    path: tuple[str, ...]
    minutes: float

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("a route needs at least one junction")
        if not self.minutes >= 0 or self.minutes == float("inf"):
            raise ValueError("a route needs a finite time of zero or more minutes")

    @property
    def source(self) -> str:
        return self.path[0]

    @property
    def target(self) -> str:
        return self.path[-1]


@dataclass(frozen=True, slots=True)
class _RouteSpace:
    """A road network seen as a SearchSpace for one start and one goal."""

    network: RoadNetwork
    start: str
    goal: str

    def neighbors(self, node: str, /) -> tuple[str, ...]:
        return self.network.neighbors(node)

    def step_cost(self, source: str, target: str, /) -> float:
        return self.network.travel_minutes(source, target)


def _fastest_speed(network: RoadNetwork) -> float:
    """The most straight-line distance any single road covers per minute."""
    return max(
        (
            network.distance(road.source, road.target) / road.minutes
            for road in network.roads
        ),
        default=0.0,
    )


def route_events(
    network: RoadNetwork, source: str, target: str
) -> Iterator[AlgorithmEvent]:
    """The A* events for the fastest route from ``source`` to ``target``."""
    known = {junction.id for junction in network.junctions}
    for name in (source, target):
        if name not in known:
            raise ValueError(f"unknown junction {name!r}")

    speed = _fastest_speed(network)

    def estimate(node: str) -> float:
        if speed == 0:
            return 0.0
        return network.distance(node, target) / speed

    return best_first(_RouteSpace(network, source, target), estimate)


def find_route(network: RoadNetwork, source: str, target: str) -> Route | None:
    """The fastest route, or None when ``target`` cannot be reached."""
    for event in route_events(network, source, target):
        if event.kind is EventType.PATH_FOUND:
            if event.path is None or event.cost is None:
                raise ValueError("a PATH_FOUND event must carry a path and a cost")
            return Route(cast("tuple[str, ...]", event.path), event.cost)
    return None

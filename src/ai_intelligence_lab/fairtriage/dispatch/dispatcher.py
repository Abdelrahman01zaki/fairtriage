"""Choosing which ambulance to send to an incident.

Every ambulance in the fleet is a candidate. Its arrival time is the fastest
route from its base to the scene on the road network, so one-way roads and
closed roads count. An ambulance with no route to the scene is left out.
Which ambulances are free at a given moment is for the simulation to decide,
not for this module.
"""

from collections.abc import Iterable
from dataclasses import dataclass

from ai_intelligence_lab.environments.road_network import RoadNetwork
from ai_intelligence_lab.fairtriage.dispatch.routing import Route, find_route
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance


@dataclass(frozen=True, slots=True)
class Dispatch:
    """An ambulance paired with its fastest route to the scene."""

    ambulance: Ambulance
    route: Route

    def __post_init__(self) -> None:
        if self.route.source != self.ambulance.base:
            raise ValueError(
                f"the route starts at {self.route.source!r} but ambulance "
                f"{self.ambulance.id!r} is based at {self.ambulance.base!r}"
            )

    @property
    def minutes(self) -> float:
        return self.route.minutes


def arrival_options(
    network: RoadNetwork, ambulances: Iterable[Ambulance], location: str
) -> tuple[Dispatch, ...]:
    """Every ambulance that can reach ``location``, fastest first.

    Equal times are ordered by ambulance id, so the result is repeatable.
    """
    fleet = tuple(ambulances)
    ids = [ambulance.id for ambulance in fleet]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate ambulance id in the fleet")

    options: list[Dispatch] = []
    for ambulance in fleet:
        route = find_route(network, ambulance.base, location)
        if route is not None:
            options.append(Dispatch(ambulance, route))
    return tuple(
        sorted(options, key=lambda option: (option.minutes, option.ambulance.id))
    )


def nearest_ambulance(
    network: RoadNetwork, ambulances: Iterable[Ambulance], location: str
) -> Dispatch | None:
    """The ambulance that arrives first, or None when none can arrive."""
    options = arrival_options(network, ambulances, location)
    return options[0] if options else None

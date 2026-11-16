"""Turning an incident into a problem the allocation core can solve.

This is the one place where FairTriage words meet the domain-free core. A
casualty becomes a demand whose priority is its START urgency, a hospital
becomes a resource whose capacity is its beds, and the cost of taking a
casualty to a hospital is the minutes of driving from the scene.

A hospital with no route from the scene gets no cost, so no allocator can send
a casualty there. Expectant (black) casualties are kept: they come last in
urgency, so they only get a bed that nobody more urgent needs.
"""

from collections.abc import Iterable

from ai_intelligence_lab.allocation.model import AllocationProblem, Demand, Resource
from ai_intelligence_lab.environments.road_network import RoadNetwork
from ai_intelligence_lab.fairtriage.dispatch.routing import find_route
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident


def build_transport_problem(
    network: RoadNetwork, incident: Incident, hospitals: Iterable[Hospital]
) -> AllocationProblem:
    """The problem of taking the incident's casualties to the hospitals."""
    fleet = tuple(hospitals)
    demands = tuple(
        Demand(
            casualty.id,
            casualty.category.urgency,
            casualty.reported_at,
            casualty.needs,
        )
        for casualty in incident.casualties
    )
    resources = tuple(
        Resource(hospital.id, hospital.beds, hospital.specialties) for hospital in fleet
    )

    cost: dict[tuple[str, str], float] = {}
    for hospital in fleet:
        route = find_route(network, incident.location, hospital.location)
        if route is None:
            continue
        for casualty in incident.casualties:
            cost[(casualty.id, hospital.id)] = route.minutes

    return AllocationProblem(demands, resources, cost)

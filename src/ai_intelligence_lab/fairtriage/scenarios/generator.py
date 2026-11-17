"""Seeded random scenarios, so policies can be compared on many incidents.

The same spec and the same seed always give the same scenario, on any run
and any machine. Nothing here iterates over a set, because the order of a
set of strings changes from one Python run to the next.

The sizes and the default category weights are illustrative. They are not
drawn from real incident data and must not be read as typical of real
incidents. A result is only worth stating over a range of specs.
"""

import math
import random
from dataclasses import dataclass

from ai_intelligence_lab.environments.road_network import Junction, Road, RoadNetwork
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.simulation.scenario import Scenario

# Junctions are placed in a square of this side. One unit of distance is one
# minute of driving, with at least one minute for any road.
_AREA = 30.0

_EQUAL_WEIGHTS = tuple((category, 1.0) for category in TriageCategory)


@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    """What kind of scenario to draw. Every default is illustrative only."""

    casualties: int = 12
    hospitals: int = 3
    beds_per_hospital: int = 4
    ambulances: int = 3
    junctions: int = 12
    extra_roads: int = 4
    report_window: float = 20.0
    category_weights: tuple[tuple[TriageCategory, float], ...] = _EQUAL_WEIGHTS

    def __post_init__(self) -> None:
        for name in ("casualties", "hospitals", "beds_per_hospital", "ambulances"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1")
        if self.junctions < 2:
            raise ValueError("junctions must be at least 2")
        if self.hospitals > self.junctions - 1:
            raise ValueError(
                "every hospital needs its own junction, apart from the scene"
            )

        pairs = self.junctions * (self.junctions - 1) // 2
        most = pairs - (self.junctions - 1)
        if not 0 <= self.extra_roads <= most:
            raise ValueError(f"extra_roads must be between 0 and {most}")
        if not math.isfinite(self.report_window) or self.report_window < 0:
            raise ValueError("report_window must be a finite time of zero or more")

        weights = tuple(self.category_weights)
        if not weights:
            raise ValueError("category_weights cannot be empty")
        seen: set[TriageCategory] = set()
        for category, weight in weights:
            if not isinstance(category, TriageCategory):
                raise ValueError("category_weights must name TriageCategory values")
            if category in seen:
                raise ValueError(f"category {category.name} is weighted twice")
            seen.add(category)
            if not math.isfinite(weight) or weight < 0:
                raise ValueError("a category weight must be finite and zero or more")
        if sum(weight for _, weight in weights) <= 0:
            raise ValueError("at least one category needs a weight above zero")
        object.__setattr__(self, "category_weights", weights)


def generate_scenario(spec: ScenarioSpec, *, seed: int = 0) -> Scenario:
    """Draw one scenario. The same ``spec`` and ``seed`` give the same one."""
    rng = random.Random(seed)
    network = _network(spec, rng)
    names = [junction.id for junction in network.junctions]

    scene = rng.choice(names)
    others = [name for name in names if name != scene]
    sites = rng.sample(others, spec.hospitals)
    hospitals = tuple(
        Hospital(f"H{number}", site, spec.beds_per_hospital)
        for number, site in enumerate(sites, start=1)
    )

    bases = rng.choices(names, k=spec.ambulances)
    ambulances = tuple(
        Ambulance(f"A{number}", base) for number, base in enumerate(bases, start=1)
    )

    # A zero weight can never be drawn, so such a category is left out.
    kinds = [category for category, weight in spec.category_weights if weight > 0]
    weights = [weight for _, weight in spec.category_weights if weight > 0]
    categories = rng.choices(kinds, weights=weights, k=spec.casualties)
    casualties = tuple(
        Casualty(f"C{number}", category, round(rng.uniform(0.0, spec.report_window), 1))
        for number, category in enumerate(categories, start=1)
    )

    incident = Incident(f"S{seed}", scene, casualties)
    return Scenario(network, incident, hospitals, ambulances)


def _gap(first: Junction, second: Junction) -> float:
    return math.hypot(first.x - second.x, first.y - second.y)


def _nearest_earlier(junctions: tuple[Junction, ...], later: int) -> int:
    """Index of the closest junction before ``later``; the lower index on a tie."""
    return min(
        range(later),
        key=lambda earlier: (_gap(junctions[earlier], junctions[later]), earlier),
    )


def _network(spec: ScenarioSpec, rng: random.Random) -> RoadNetwork:
    """A connected road network.

    Each junction after the first is joined to the nearest one before it, which
    makes a tree, so every junction can be reached. Then ``extra_roads`` more
    roads are added between junctions that are not yet joined.
    """
    junctions = tuple(
        Junction(
            f"J{number}",
            round(rng.uniform(0.0, _AREA), 1),
            round(rng.uniform(0.0, _AREA), 1),
        )
        for number in range(1, spec.junctions + 1)
    )

    links = [
        (_nearest_earlier(junctions, later), later)
        for later in range(1, len(junctions))
    ]
    joined = set(links)  # only asked "is this pair in it", never iterated
    free = [
        (first, second)
        for first in range(len(junctions))
        for second in range(first + 1, len(junctions))
        if (first, second) not in joined
    ]
    links += rng.sample(free, spec.extra_roads)

    roads = tuple(
        Road(
            junctions[first].id,
            junctions[second].id,
            max(1.0, round(_gap(junctions[first], junctions[second]), 1)),
        )
        for first, second in links
    )
    return RoadNetwork(junctions, roads)

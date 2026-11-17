"""How fairly one simulation run treated its casualties.

Casualties are compared only with others of the same START category. A red
casualty waiting less than a green one is the medical order, not unfairness.
What counts as unfair is two casualties of the same category who waited very
different times, or who were never served at all.

Waiting time is the time from being reported until an ambulance reached the
casualty, as ``Transport.waited`` states it.
"""

import math
import statistics
from collections.abc import Sequence
from dataclasses import dataclass

from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.simulation.scenario import SimulationResult


def gini(values: Sequence[float]) -> float:
    """Inequality of ``values``: 0 when all are equal, near 1 when one has all.

    An empty list, or a list of zeros, has no inequality.
    """
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("gini needs finite values of zero or more")
    count = len(values)
    total = sum(values)
    if count == 0 or total == 0:
        return 0.0
    ordered = sorted(values)
    weighted = sum(rank * value for rank, value in enumerate(ordered, start=1))
    # Rounding can leave a tiny negative number for equal values.
    return max(0.0, 2 * weighted / (count * total) - (count + 1) / count)


@dataclass(frozen=True, slots=True)
class CategoryFairness:
    """How one START category fared.

    Waits and times to hospital are None when nobody was served. Every wait,
    time and gini here is over the transported casualties only, so read it
    together with ``served_fraction``: a policy that serves fewer can look better.
    """

    category: TriageCategory
    transported: int
    unserved: int
    mean_wait: float | None
    median_wait: float | None
    worst_wait: float | None
    gini: float
    mean_to_hospital: float | None = None
    worst_to_hospital: float | None = None

    @property
    def served_fraction(self) -> float:
        """Share of this category's casualties that were transported."""
        total = self.transported + self.unserved
        return self.transported / total if total else 0.0


@dataclass(frozen=True, slots=True)
class FairnessReport:
    """One row per category that has casualties, most urgent category first."""

    categories: tuple[CategoryFairness, ...]

    @property
    def unserved_total(self) -> int:
        return sum(item.unserved for item in self.categories)

    def category(self, category: TriageCategory) -> CategoryFairness | None:
        for item in self.categories:
            if item.category is category:
                return item
        return None


def fairness_report(incident: Incident, result: SimulationResult) -> FairnessReport:
    """Measure ``result`` against the casualties of ``incident``."""
    known = {casualty.id: casualty for casualty in incident.casualties}
    waits: dict[TriageCategory, list[float]] = {}
    trips: dict[TriageCategory, list[float]] = {}
    unserved: dict[TriageCategory, int] = {}

    for transport in result.transports:
        casualty = known.get(transport.casualty_id)
        if casualty is None:
            raise ValueError(f"unknown casualty {transport.casualty_id!r}")
        if casualty.category is not transport.category:
            raise ValueError(
                f"casualty {casualty.id!r} is {casualty.category.name} "
                f"but was transported as {transport.category.name}"
            )
        waits.setdefault(casualty.category, []).append(transport.waited)
        trips.setdefault(casualty.category, []).append(transport.time_to_hospital)

    for casualty_id in result.unserved:
        casualty = known.get(casualty_id)
        if casualty is None:
            raise ValueError(f"unknown casualty {casualty_id!r}")
        unserved[casualty.category] = unserved.get(casualty.category, 0) + 1

    present = {casualty.category for casualty in incident.casualties}
    rows: list[CategoryFairness] = []
    for category in sorted(present, key=lambda item: item.urgency):
        values = waits.get(category, [])
        trip = trips.get(category, [])
        rows.append(
            CategoryFairness(
                category,
                len(values),
                unserved.get(category, 0),
                statistics.mean(values) if values else None,
                statistics.median(values) if values else None,
                max(values) if values else None,
                gini(values),
                statistics.mean(trip) if trip else None,
                max(trip) if trip else None,
            )
        )
    return FairnessReport(tuple(rows))


def waits_to_horizon(
    incident: Incident, result: SimulationResult, horizon: float
) -> dict[TriageCategory, tuple[float, ...]]:
    """Each casualty's wait, with the clock stopped at ``horizon``.

    ``horizon`` is in minutes since the incident began. A casualty never served,
    or served after it, counts as ``horizon - reported_at``: nobody drops out of
    the measure because a policy left them unserved.
    """
    if not math.isfinite(horizon) or horizon <= 0:
        raise ValueError("horizon must be a finite time above zero")
    known = {casualty.id for casualty in incident.casualties}
    served = {transport.casualty_id: transport for transport in result.transports}
    stranger = set(served) - known
    if stranger:
        raise ValueError(f"unknown casualty {sorted(stranger)[0]!r}")

    waits: dict[TriageCategory, list[float]] = {}
    for casualty in incident.casualties:
        if casualty.reported_at > horizon:
            raise ValueError(f"casualty {casualty.id!r} was reported after the horizon")
        cap = horizon - casualty.reported_at
        transport = served.get(casualty.id)
        wait = cap if transport is None else min(transport.waited, cap)
        waits.setdefault(casualty.category, []).append(wait)
    return {
        category: tuple(waits[category])
        for category in sorted(waits, key=lambda item: item.urgency)
    }


@dataclass(frozen=True, slots=True)
class HorizonWaits:
    """One category's waits over every casualty, with the clock stopped at a horizon.

    ``gini`` is None for a single casualty: one value has no inequality to measure.
    Equal waits give 0.0 even when nobody was served, so read it together with
    ``served_fraction``: it says how evenly the waiting was shared, not whether
    anyone was helped.
    """

    category: TriageCategory
    count: int
    mean_wait: float
    gini: float | None


def horizon_fairness(
    incident: Incident, result: SimulationResult, horizon: float
) -> tuple[HorizonWaits, ...]:
    """Mean wait and gini per category over all casualties, most urgent first."""
    return tuple(
        HorizonWaits(
            category,
            len(values),
            statistics.mean(values),
            gini(values) if len(values) >= 2 else None,
        )
        for category, values in waits_to_horizon(incident, result, horizon).items()
    )

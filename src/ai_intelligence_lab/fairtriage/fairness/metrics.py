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
    """How one START category fared. Waits are None when nobody was served."""

    category: TriageCategory
    transported: int
    unserved: int
    mean_wait: float | None
    median_wait: float | None
    worst_wait: float | None
    gini: float


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

    for casualty_id in result.unserved:
        casualty = known.get(casualty_id)
        if casualty is None:
            raise ValueError(f"unknown casualty {casualty_id!r}")
        unserved[casualty.category] = unserved.get(casualty.category, 0) + 1

    present = {casualty.category for casualty in incident.casualties}
    rows: list[CategoryFairness] = []
    for category in sorted(present, key=lambda item: item.urgency):
        values = waits.get(category, [])
        rows.append(
            CategoryFairness(
                category,
                len(values),
                unserved.get(category, 0),
                statistics.mean(values) if values else None,
                statistics.median(values) if values else None,
                max(values) if values else None,
                gini(values),
            )
        )
    return FairnessReport(tuple(rows))

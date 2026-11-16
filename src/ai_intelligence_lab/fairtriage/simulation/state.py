"""The world at one moment: where each ambulance is and how full each hospital is.

The state only records. It never decides who goes where. Every change returns
a new state and leaves the old one as it was, so a run can be replayed and
compared step by step.

Times are minutes since the incident began, like ``Casualty.reported_at``.
"""

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType

from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital


@dataclass(frozen=True, slots=True)
class AmbulanceStatus:
    """An ambulance, the junction it is at, and when it is free there."""

    ambulance: Ambulance
    location: str
    free_at: float = 0.0

    def __post_init__(self) -> None:
        if not self.location:
            raise ValueError(f"ambulance {self.ambulance.id!r} needs a location")
        if not math.isfinite(self.free_at) or self.free_at < 0:
            raise ValueError(
                f"ambulance {self.ambulance.id!r}: free_at must be a finite "
                "time of zero or more minutes"
            )

    def is_free(self, now: float) -> bool:
        return self.free_at <= now


@dataclass(frozen=True, slots=True)
class WorldState:
    """Every ambulance and every hospital, with the beds taken at each hospital.

    A hospital missing from ``occupied`` has no beds taken.
    """

    ambulances: tuple[AmbulanceStatus, ...]
    hospitals: tuple[Hospital, ...]
    occupied: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        ambulances = tuple(self.ambulances)
        hospitals = tuple(self.hospitals)
        _require_unique("ambulance id", (item.ambulance.id for item in ambulances))
        _require_unique("hospital id", (hospital.id for hospital in hospitals))

        beds = {hospital.id: hospital.beds for hospital in hospitals}
        taken_now = dict.fromkeys(beds, 0)
        for hospital_id, taken in dict(self.occupied).items():
            if hospital_id not in beds:
                raise ValueError(f"beds given for unknown hospital {hospital_id!r}")
            if not 0 <= taken <= beds[hospital_id]:
                raise ValueError(
                    f"hospital {hospital_id!r} has {beds[hospital_id]} beds "
                    f"but {taken} are marked as taken"
                )
            taken_now[hospital_id] = taken

        # Freeze private copies, as Grid does.
        object.__setattr__(self, "ambulances", ambulances)
        object.__setattr__(self, "hospitals", hospitals)
        object.__setattr__(self, "occupied", MappingProxyType(taken_now))

    @classmethod
    def start(
        cls, ambulances: Iterable[Ambulance], hospitals: Iterable[Hospital]
    ) -> "WorldState":
        """The world at the beginning: every ambulance free at its base."""
        return cls(
            tuple(AmbulanceStatus(item, item.base) for item in ambulances),
            tuple(hospitals),
        )

    def status_of(self, ambulance_id: str) -> AmbulanceStatus:
        for status in self.ambulances:
            if status.ambulance.id == ambulance_id:
                return status
        raise ValueError(f"unknown ambulance {ambulance_id!r}")

    def free_beds(self, hospital_id: str) -> int:
        for hospital in self.hospitals:
            if hospital.id == hospital_id:
                return hospital.beds - self.occupied[hospital_id]
        raise ValueError(f"unknown hospital {hospital_id!r}")

    def available_ambulances(self, now: float) -> tuple[Ambulance, ...]:
        """The ambulances free at ``now``, each placed where it is now.

        The place is stored as ``base``, so the dispatcher can route from where
        the ambulance really is. Match them back to the fleet by ``id``.
        """
        return tuple(
            Ambulance(item.ambulance.id, item.location)
            for item in self.ambulances
            if item.is_free(now)
        )

    def with_ambulance(
        self, ambulance_id: str, location: str, free_at: float
    ) -> "WorldState":
        """A new state where one ambulance is at ``location``, free at ``free_at``."""
        self.status_of(ambulance_id)
        updated = tuple(
            AmbulanceStatus(item.ambulance, location, free_at)
            if item.ambulance.id == ambulance_id
            else item
            for item in self.ambulances
        )
        return replace(self, ambulances=updated)

    def with_admission(self, hospital_id: str) -> "WorldState":
        """A new state where one more bed is taken at ``hospital_id``."""
        if self.free_beds(hospital_id) == 0:
            raise ValueError(f"hospital {hospital_id!r} has no free bed")
        taken = dict(self.occupied)
        taken[hospital_id] += 1
        return replace(self, occupied=taken)


def _require_unique(what: str, ids: Iterable[str]) -> None:
    seen: set[str] = set()
    for item in ids:
        if item in seen:
            raise ValueError(f"duplicate {what}: {item!r}")
        seen.add(item)

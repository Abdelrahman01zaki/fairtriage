"""An incident: one event that produced casualties at one place.

``location`` names a point on the road network, like ``Hospital.location``.
Hospitals and ambulances are resources of the simulation, not part of the
incident, so they are not stored here.
"""

from dataclasses import dataclass

from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory


@dataclass(frozen=True, slots=True)
class Incident:
    id: str
    location: str
    casualties: tuple[Casualty, ...]

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("an incident needs an id")
        if not self.location:
            raise ValueError(f"incident {self.id!r} needs a location")
        if isinstance(self.casualties, str):
            raise ValueError(f"incident {self.id!r}: casualties must be a collection")

        casualties = tuple(self.casualties)
        if not casualties:
            raise ValueError(f"incident {self.id!r} needs at least one casualty")
        if not all(isinstance(item, Casualty) for item in casualties):
            raise ValueError(f"incident {self.id!r}: every casualty must be a Casualty")
        ids = [item.id for item in casualties]
        if len(set(ids)) != len(ids):
            raise ValueError(f"incident {self.id!r} has duplicate casualty ids")

        object.__setattr__(self, "casualties", casualties)

    def in_category(self, category: TriageCategory) -> tuple[Casualty, ...]:
        """The casualties in ``category``, in the order they were given."""
        return tuple(item for item in self.casualties if item.category is category)

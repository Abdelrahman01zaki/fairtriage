"""A hospital: a place casualties are taken to, with a limited number of beds.

``location`` names a point on the road network. ``beds`` is the total
capacity; how many are taken at a given moment belongs to the simulation, not
to this description.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Hospital:
    id: str
    location: str
    beds: int
    specialties: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("a hospital needs an id")
        if not self.location:
            raise ValueError(f"hospital {self.id!r} needs a location")
        if self.beds <= 0:
            raise ValueError(f"hospital {self.id!r} needs a positive number of beds")
        if isinstance(self.specialties, str):
            raise ValueError(f"hospital {self.id!r}: specialties must be a collection")
        object.__setattr__(self, "specialties", frozenset(self.specialties))

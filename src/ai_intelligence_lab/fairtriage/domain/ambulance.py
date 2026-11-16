"""An ambulance and the base it starts from.

``base`` names a point on the road network, like ``Hospital.location``.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Ambulance:
    id: str
    base: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("an ambulance needs an id")
        if not self.base:
            raise ValueError(f"ambulance {self.id!r} needs a base")

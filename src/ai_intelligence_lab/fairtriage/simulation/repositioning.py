"""Where an ambulance waits after it has left a casualty at a hospital.

Every policy has the same shape, so a simulation can take any of them, or a
new one, without changes:

return_to_base    drive back to the base, to cover the usual area
stay_at_hospital  wait where it is, which is quick to reach a scene still open
adaptive          stay while casualties still wait, otherwise return to base

A policy only chooses the place. How long the drive takes, and whether the
ambulance can be called while it is driving, is for the simulation to decide.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance


@dataclass(frozen=True, slots=True)
class RepositionContext:
    """What a policy may look at: the ambulance, where it is, who still waits."""

    ambulance: Ambulance
    at: str
    pending: int

    def __post_init__(self) -> None:
        if not self.at:
            raise ValueError(f"ambulance {self.ambulance.id!r} needs a location")
        if self.pending < 0:
            raise ValueError("the number of waiting casualties cannot be negative")


Repositioning = Callable[[RepositionContext], str]


def return_to_base(context: RepositionContext) -> str:
    return context.ambulance.base


def stay_at_hospital(context: RepositionContext) -> str:
    return context.at


def adaptive(context: RepositionContext) -> str:
    """Stay while someone still waits, since the scene is closer from here."""
    return context.at if context.pending > 0 else context.ambulance.base


POLICIES: Mapping[str, Repositioning] = MappingProxyType(
    {
        "return_to_base": return_to_base,
        "stay_at_hospital": stay_at_hospital,
        "adaptive": adaptive,
    }
)

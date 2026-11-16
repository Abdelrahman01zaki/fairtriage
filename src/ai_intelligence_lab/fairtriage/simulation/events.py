"""Things that happen during a simulation, as the queue carries them.

CasualtyReported   a casualty becomes known and starts to wait
AmbulanceDelivered an ambulance reaches the hospital with a casualty
AmbulanceFree      an ambulance finished driving back and can be sent again

``at`` in ``AmbulanceDelivered`` is the junction of the hospital.
"""

from dataclasses import dataclass

from ai_intelligence_lab.fairtriage.domain.casualty import Casualty


@dataclass(frozen=True, slots=True)
class CasualtyReported:
    casualty: Casualty


@dataclass(frozen=True, slots=True)
class AmbulanceDelivered:
    ambulance_id: str
    at: str


@dataclass(frozen=True, slots=True)
class AmbulanceFree:
    ambulance_id: str


SimulationEvent = CasualtyReported | AmbulanceDelivered | AmbulanceFree

"""What a simulation starts from, and what it gives back.

A scenario is one incident, the hospitals and ambulances that can respond to
it, and the road network they drive on. A transport is the record of one
casualty carried to a hospital, with the time of every step, so waiting time
and fairness can be measured afterwards without running anything again.
"""

import math
from dataclasses import dataclass

from ai_intelligence_lab.environments.road_network import RoadNetwork
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.simulation.state import WorldState


@dataclass(frozen=True, slots=True)
class Scenario:
    network: RoadNetwork
    incident: Incident
    hospitals: tuple[Hospital, ...]
    ambulances: tuple[Ambulance, ...]

    def __post_init__(self) -> None:
        hospitals = tuple(self.hospitals)
        ambulances = tuple(self.ambulances)
        if not hospitals:
            raise ValueError("a scenario needs at least one hospital")
        if not ambulances:
            raise ValueError("a scenario needs at least one ambulance")
        # Building the starting state also rejects duplicate ids.
        WorldState.start(ambulances, hospitals)

        known = {junction.id for junction in self.network.junctions}
        places = [(f"incident {self.incident.id!r}", self.incident.location)]
        places += [(f"hospital {item.id!r}", item.location) for item in hospitals]
        places += [(f"ambulance {item.id!r}", item.base) for item in ambulances]
        for who, place in places:
            if place not in known:
                raise ValueError(
                    f"{who} is at {place!r}, which is not on the road network"
                )

        object.__setattr__(self, "hospitals", hospitals)
        object.__setattr__(self, "ambulances", ambulances)


@dataclass(frozen=True, slots=True)
class Transport:
    """One casualty carried to one hospital by one ambulance.

    ``waited`` is how long the casualty waited for an ambulance to reach it.
    """

    casualty_id: str
    category: TriageCategory
    ambulance_id: str
    hospital_id: str
    reported_at: float
    dispatched_at: float
    picked_up_at: float
    delivered_at: float

    def __post_init__(self) -> None:
        for name, value in (
            ("casualty_id", self.casualty_id),
            ("ambulance_id", self.ambulance_id),
            ("hospital_id", self.hospital_id),
        ):
            if not value:
                raise ValueError(f"a transport needs a {name}")
        times = [
            self.reported_at,
            self.dispatched_at,
            self.picked_up_at,
            self.delivered_at,
        ]
        if not all(math.isfinite(time) for time in times) or times != sorted(times):
            raise ValueError(
                f"transport of {self.casualty_id!r}: times must be finite and "
                "go from reported to dispatched to picked up to delivered"
            )

    @property
    def waited(self) -> float:
        return self.picked_up_at - self.reported_at


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Every transport in the order it was sent, who was never served, the end."""

    transports: tuple[Transport, ...]
    unserved: tuple[str, ...]
    final_state: WorldState
    end_time: float

    def __post_init__(self) -> None:
        transports = tuple(self.transports)
        unserved = tuple(self.unserved)
        ids = [item.casualty_id for item in transports] + list(unserved)
        if len(set(ids)) != len(ids):
            raise ValueError("a casualty appears more than once in the result")
        object.__setattr__(self, "transports", transports)
        object.__setattr__(self, "unserved", unserved)

    def transport_of(self, casualty_id: str) -> Transport | None:
        for item in self.transports:
            if item.casualty_id == casualty_id:
                return item
        return None

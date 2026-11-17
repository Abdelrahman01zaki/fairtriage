"""The simulation loop: casualties are reported, ambulances carry them away.

At every moment something happens, the loop first takes in everything that
happens at that moment, then sends ambulances while there is a free ambulance
and a casualty it can take. The most urgent casualty goes first. Which
hospital it goes to is decided by the allocator, so a smarter allocator can be
plugged in without touching this loop.

The loop knows only what has been reported so far. A bed is held for a
casualty from the moment it is sent, so a hospital is never over-booked. A
casualty that never gets a place is listed as unserved when the run ends.
"""

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.model import Allocator, Placement
from ai_intelligence_lab.allocation.validation import validate_allocation
from ai_intelligence_lab.fairtriage.dispatch.dispatcher import Dispatch, arrival_options
from ai_intelligence_lab.fairtriage.dispatch.routing import find_route
from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.simulation.events import (
    AmbulanceDelivered,
    AmbulanceFree,
    CasualtyReported,
    SimulationEvent,
)
from ai_intelligence_lab.fairtriage.simulation.repositioning import (
    RepositionContext,
    Repositioning,
    return_to_base,
)
from ai_intelligence_lab.fairtriage.simulation.scenario import (
    Scenario,
    SimulationResult,
    Transport,
)
from ai_intelligence_lab.fairtriage.simulation.state import WorldState
from ai_intelligence_lab.fairtriage.transport.priority import PriorityRule, by_urgency
from ai_intelligence_lab.fairtriage.transport.problem import (
    build_transport_problem,
)
from ai_intelligence_lab.simulation.event_queue import EventQueue


def simulate(
    scenario: Scenario,
    *,
    allocator: Allocator = greedy_allocate,
    repositioning: Repositioning = return_to_base,
    priority: PriorityRule = by_urgency,
) -> SimulationResult:
    """Run the scenario to the end and return everything that happened.

    ``priority`` decides who is served first; the default is START urgency.
    """
    return _Run(scenario, allocator, repositioning, priority).execute()


class _Run:
    def __init__(
        self,
        scenario: Scenario,
        allocator: Allocator,
        repositioning: Repositioning,
        priority: PriorityRule,
    ) -> None:
        self._scenario = scenario
        self._allocator = allocator
        self._repositioning = repositioning
        self._priority = priority
        self._hospitals = {item.id: item for item in scenario.hospitals}
        self._queue: EventQueue[SimulationEvent] = EventQueue()
        self._state = WorldState.start(scenario.ambulances, scenario.hospitals)
        self._waiting: dict[str, Casualty] = {}
        self._transports: list[Transport] = []
        for casualty in scenario.incident.casualties:
            self._queue.schedule(casualty.reported_at, CasualtyReported(casualty))

    def _order(self, casualty: Casualty) -> tuple[int, float, str]:
        return (self._priority(casualty), casualty.reported_at, casualty.id)

    def execute(self) -> SimulationResult:
        while len(self._queue) > 0:
            first = self._queue.pop()
            now = first.time
            self._apply(first.payload, now)
            while self._queue.peek_time() == now:
                self._apply(self._queue.pop().payload, now)
            self._dispatch(now)

        left = sorted(self._waiting.values(), key=self._order)
        unserved = tuple(casualty.id for casualty in left)

        return SimulationResult(
            tuple(self._transports), unserved, self._state, self._queue.now
        )

    def _apply(self, event: SimulationEvent, now: float) -> None:
        if isinstance(event, CasualtyReported):
            self._waiting[event.casualty.id] = event.casualty
        elif isinstance(event, AmbulanceDelivered):
            self._reposition(event, now)
        # AmbulanceFree changes nothing: it only makes the loop decide again.

    def _reposition(self, event: AmbulanceDelivered, now: float) -> None:
        status = self._state.status_of(event.ambulance_id)
        context = RepositionContext(status.ambulance, event.at, len(self._waiting))
        place = self._repositioning(context)

        free_at = now
        if place != event.at:
            route = find_route(self._scenario.network, event.at, place)
            if route is None:
                place = event.at
            else:
                free_at = now + route.minutes

        self._state = self._state.with_ambulance(event.ambulance_id, place, free_at)
        if free_at > now:
            self._queue.schedule(free_at, AmbulanceFree(event.ambulance_id))

    def _dispatch(self, now: float) -> None:
        while self._waiting:
            plan = self._plan(now)
            if plan is None:
                return
            casualty, dispatch, placement = plan
            self._send(casualty, dispatch, placement, now)

    def _plan(self, now: float) -> tuple[Casualty, Dispatch, Placement] | None:
        """The next casualty to send, with its ambulance and hospital, if any."""
        scenario = self._scenario
        free = self._state.available_ambulances(now)
        options = arrival_options(scenario.network, free, scenario.incident.location)
        if not options:
            return None

        open_hospitals = tuple(
            Hospital(item.id, item.location, beds, item.specialties)
            for item in self._state.hospitals
            if (beds := self._state.free_beds(item.id)) > 0
        )
        if not open_hospitals:
            return None

        waiting = tuple(sorted(self._waiting.values(), key=self._order))
        incident = Incident(scenario.incident.id, scenario.incident.location, waiting)
        problem = build_transport_problem(
            scenario.network, incident, open_hospitals, priority=self._priority
        )
        allocation = self._allocator(problem)
        validate_allocation(problem, allocation)

        for casualty in waiting:
            placement = allocation.placement_of(casualty.id)
            if placement is not None:
                return casualty, options[0], placement
        return None

    def _send(
        self, casualty: Casualty, dispatch: Dispatch, placement: Placement, now: float
    ) -> None:
        hospital = self._hospitals[placement.resource_id]
        ambulance_id = dispatch.ambulance.id
        picked_up = now + dispatch.minutes
        delivered = picked_up + placement.cost

        del self._waiting[casualty.id]
        self._state = self._state.with_admission(hospital.id).with_ambulance(
            ambulance_id, hospital.location, delivered
        )
        self._queue.schedule(
            delivered, AmbulanceDelivered(ambulance_id, hospital.location)
        )
        self._transports.append(
            Transport(
                casualty.id,
                casualty.category,
                ambulance_id,
                hospital.id,
                casualty.reported_at,
                now,
                picked_up,
                delivered,
            )
        )

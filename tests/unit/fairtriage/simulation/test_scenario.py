import pytest

from ai_intelligence_lab.environments.road_network import Junction, Road, RoadNetwork
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.simulation.scenario import (
    Scenario,
    SimulationResult,
    Transport,
)
from ai_intelligence_lab.fairtriage.simulation.state import WorldState

NETWORK = RoadNetwork(
    (Junction("A", 0.0, 0.0), Junction("B", 5.0, 0.0)),
    (Road("A", "B", 5.0),),
)
INCIDENT = Incident("I-1", "A", (Casualty("C-1", TriageCategory.RED, 0.0),))
HOSPITAL = Hospital("H-1", "B", 3)
AMBULANCE = Ambulance("A-1", "A")


def make_transport(**changes):
    values = {
        "casualty_id": "C-1",
        "category": TriageCategory.RED,
        "ambulance_id": "A-1",
        "hospital_id": "H-1",
        "reported_at": 0.0,
        "dispatched_at": 1.0,
        "picked_up_at": 6.0,
        "delivered_at": 11.0,
    }
    values.update(changes)
    return Transport(**values)


def test_a_valid_scenario_is_accepted():
    scenario = Scenario(NETWORK, INCIDENT, [HOSPITAL], [AMBULANCE])

    assert scenario.hospitals == (HOSPITAL,)
    assert scenario.ambulances == (AMBULANCE,)


def test_a_scenario_needs_a_hospital_and_an_ambulance():
    with pytest.raises(ValueError):
        Scenario(NETWORK, INCIDENT, (), (AMBULANCE,))
    with pytest.raises(ValueError):
        Scenario(NETWORK, INCIDENT, (HOSPITAL,), ())


@pytest.mark.parametrize(
    ("incident", "hospital", "ambulance"),
    [
        (Incident("I-2", "Z", INCIDENT.casualties), HOSPITAL, AMBULANCE),
        (INCIDENT, Hospital("H-2", "Z", 1), AMBULANCE),
        (INCIDENT, HOSPITAL, Ambulance("A-2", "Z")),
    ],
    ids=["incident", "hospital", "ambulance"],
)
def test_every_place_must_be_on_the_road_network(incident, hospital, ambulance):
    with pytest.raises(ValueError, match="road network"):
        Scenario(NETWORK, incident, (hospital,), (ambulance,))


def test_duplicate_ids_are_rejected():
    with pytest.raises(ValueError):
        Scenario(NETWORK, INCIDENT, (HOSPITAL,), (AMBULANCE, AMBULANCE))


def test_a_transport_knows_how_long_the_casualty_waited():
    assert make_transport().waited == 6.0


def test_transport_times_must_be_in_order():
    with pytest.raises(ValueError):
        make_transport(dispatched_at=7.0)
    with pytest.raises(ValueError):
        make_transport(reported_at=2.0)


def test_transport_times_must_be_finite():
    with pytest.raises(ValueError):
        make_transport(delivered_at=float("inf"))
    with pytest.raises(ValueError):
        make_transport(picked_up_at=float("nan"))


@pytest.mark.parametrize("name", ["casualty_id", "ambulance_id", "hospital_id"])
def test_a_transport_needs_its_ids(name):
    with pytest.raises(ValueError):
        make_transport(**{name: ""})


def test_a_result_finds_a_transport_by_casualty():
    state = WorldState.start([AMBULANCE], [HOSPITAL])
    transport = make_transport()
    result = SimulationResult([transport], ["C-2"], state, 11.0)

    assert result.transport_of("C-1") == transport
    assert result.transport_of("C-2") is None
    assert result.unserved == ("C-2",)


def test_a_casualty_cannot_be_both_transported_and_unserved():
    state = WorldState.start([AMBULANCE], [HOSPITAL])

    with pytest.raises(ValueError):
        SimulationResult((make_transport(),), ("C-1",), state, 11.0)

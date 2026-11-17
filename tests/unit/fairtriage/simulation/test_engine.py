import pytest

from ai_intelligence_lab.allocation.model import Allocation, Unplaced
from ai_intelligence_lab.environments.road_network import Junction, Road, RoadNetwork
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.simulation.engine import simulate
from ai_intelligence_lab.fairtriage.simulation.repositioning import (
    adaptive,
    stay_at_hospital,
)
from ai_intelligence_lab.fairtriage.simulation.scenario import Scenario
from ai_intelligence_lab.fairtriage.transport.priority import fifo

# BASE --10-- SCENE --4-- H1      SCENE --8-- H2      ISLAND has no road.
NETWORK = RoadNetwork(
    (
        Junction("BASE", 0.0, 0.0),
        Junction("SCENE", 10.0, 0.0),
        Junction("H1", 14.0, 0.0),
        Junction("H2", 10.0, -8.0),
        Junction("ISLAND", 50.0, 50.0),
    ),
    (
        Road("BASE", "SCENE", 10.0),
        Road("SCENE", "H1", 4.0),
        Road("SCENE", "H2", 8.0),
    ),
)
NEAR = Hospital("HOSP-1", "H1", 5)
FAR = Hospital("HOSP-2", "H2", 5)
ONE_AMBULANCE = (Ambulance("A1", "BASE"),)


def casualty(name, category=TriageCategory.RED, at=0.0, needs=()):
    return Casualty(name, category, at, frozenset(needs))


def build(*casualties, hospitals=(NEAR,), ambulances=ONE_AMBULANCE):
    incident = Incident("I-1", "SCENE", casualties)
    return Scenario(NETWORK, incident, hospitals, ambulances)


def test_one_casualty_is_carried_with_the_expected_times():
    result = simulate(build(casualty("C1")))

    transport = result.transport_of("C1")
    assert (transport.ambulance_id, transport.hospital_id) == ("A1", "HOSP-1")
    assert transport.dispatched_at == 0.0
    assert transport.picked_up_at == 10.0
    assert transport.delivered_at == 14.0
    assert transport.waited == 10.0
    assert result.unserved == ()


def test_the_hospital_bed_is_taken():
    result = simulate(build(casualty("C1")))

    assert result.final_state.free_beds("HOSP-1") == 4


def test_by_default_the_ambulance_drives_back_to_its_base():
    result = simulate(build(casualty("C1")))

    status = result.final_state.status_of("A1")
    assert status.location == "BASE"
    assert status.free_at == 28.0
    assert result.end_time == 28.0


def test_an_ambulance_can_stay_at_the_hospital_instead():
    result = simulate(build(casualty("C1")), repositioning=stay_at_hospital)

    status = result.final_state.status_of("A1")
    assert status.location == "H1"
    assert status.free_at == 14.0
    assert result.end_time == 14.0


def test_the_most_urgent_casualty_is_sent_first():
    scenario = build(
        casualty("G", TriageCategory.GREEN),
        casualty("R", TriageCategory.RED),
    )

    result = simulate(scenario)

    assert [item.casualty_id for item in result.transports] == ["R", "G"]


def test_staying_at_the_hospital_shortens_the_wait_of_the_next_casualty():
    scenario = build(
        casualty("R", TriageCategory.RED),
        casualty("G", TriageCategory.GREEN),
    )

    back = simulate(scenario).transport_of("G")
    stay = simulate(scenario, repositioning=stay_at_hospital).transport_of("G")

    assert back.waited == 38.0
    assert stay.waited == 18.0


def test_adaptive_stays_while_someone_waits():
    scenario = build(
        casualty("R", TriageCategory.RED),
        casualty("G", TriageCategory.GREEN),
    )

    result = simulate(scenario, repositioning=adaptive)

    assert result.transport_of("G").waited == 18.0


def test_adaptive_goes_back_to_base_when_nobody_waits():
    result = simulate(build(casualty("C1")), repositioning=adaptive)

    assert result.final_state.status_of("A1").location == "BASE"


def test_the_nearest_ambulance_is_sent():
    ambulances = (Ambulance("A1", "BASE"), Ambulance("A2", "H1"))
    scenario = build(
        casualty("R", TriageCategory.RED),
        casualty("G", TriageCategory.GREEN),
        ambulances=ambulances,
    )

    result = simulate(scenario)

    red, green = result.transport_of("R"), result.transport_of("G")
    assert (red.ambulance_id, red.picked_up_at) == ("A2", 4.0)
    assert (green.ambulance_id, green.picked_up_at) == ("A1", 10.0)
    assert red.dispatched_at == green.dispatched_at == 0.0


def test_a_full_hospital_sends_the_next_casualty_elsewhere():
    scenario = build(
        casualty("C1"),
        casualty("C2"),
        hospitals=(Hospital("HOSP-1", "H1", 1), FAR),
        ambulances=(Ambulance("A1", "BASE"), Ambulance("A2", "BASE")),
    )

    result = simulate(scenario)

    first, second = result.transport_of("C1"), result.transport_of("C2")
    assert (first.hospital_id, first.delivered_at) == ("HOSP-1", 14.0)
    assert (second.hospital_id, second.delivered_at) == ("HOSP-2", 18.0)


def test_a_casualty_goes_to_a_hospital_that_offers_what_it_needs():
    burns_unit = Hospital("HOSP-2", "H2", 5, frozenset({"burns"}))
    scenario = build(
        casualty("C1", needs=["burns"]),
        hospitals=(NEAR, burns_unit),
    )

    result = simulate(scenario)

    assert result.transport_of("C1").hospital_id == "HOSP-2"


def test_a_casualty_with_no_free_bed_is_left_unserved():
    scenario = build(
        casualty("C1", TriageCategory.RED),
        casualty("C2", TriageCategory.GREEN),
        hospitals=(Hospital("HOSP-1", "H1", 1),),
    )

    result = simulate(scenario)

    assert [item.casualty_id for item in result.transports] == ["C1"]
    assert result.unserved == ("C2",)


def test_nobody_is_served_when_no_ambulance_can_reach_the_scene():
    scenario = build(casualty("C1"), ambulances=(Ambulance("A1", "ISLAND"),))

    result = simulate(scenario)

    assert result.transports == ()
    assert result.unserved == ("C1",)


def test_a_casualty_reported_later_waits_from_its_own_time():
    result = simulate(build(casualty("C1", at=20.0)))

    transport = result.transport_of("C1")
    assert transport.dispatched_at == 20.0
    assert transport.picked_up_at == 30.0
    assert transport.waited == 10.0


def test_a_custom_allocator_is_used():
    def refuse_everyone(problem):
        return Allocation(
            (), tuple(Unplaced(demand.id, "refused") for demand in problem.demands)
        )

    scenario = build(
        casualty("G", TriageCategory.GREEN),
        casualty("R", TriageCategory.RED),
    )

    result = simulate(scenario, allocator=refuse_everyone)

    assert result.transports == ()
    assert result.unserved == ("R", "G")


def test_the_same_scenario_gives_the_same_result_every_time():
    scenario = build(
        casualty("A", TriageCategory.YELLOW),
        casualty("B", TriageCategory.RED),
        casualty("C", TriageCategory.GREEN, at=3.0),
        hospitals=(NEAR, FAR),
        ambulances=(Ambulance("A1", "BASE"), Ambulance("A2", "H1")),
    )

    assert simulate(scenario).transports == simulate(scenario).transports


def test_running_a_scenario_does_not_change_it():
    scenario = build(casualty("C1"))

    simulate(scenario)

    assert scenario.hospitals == (NEAR,)
    assert scenario.ambulances == ONE_AMBULANCE
    assert len(scenario.incident.casualties) == 1


@pytest.mark.parametrize("policy", [stay_at_hospital, adaptive])
def test_every_casualty_is_either_transported_or_unserved(policy):
    scenario = build(
        casualty("A", TriageCategory.YELLOW),
        casualty("B", TriageCategory.RED),
        casualty("C", TriageCategory.GREEN),
        hospitals=(Hospital("HOSP-1", "H1", 2),),
    )

    result = simulate(scenario, repositioning=policy)

    handled = {item.casualty_id for item in result.transports} | set(result.unserved)
    assert handled == {"A", "B", "C"}


def sent_order(result):
    return [item.casualty_id for item in result.transports]


def waiting_when_the_ambulance_is_back(hospitals):
    # The only ambulance is busy until minute 28, so C2 and C3 both wait.
    return build(
        casualty("C1", TriageCategory.GREEN),
        casualty("C2", TriageCategory.GREEN, at=1.0),
        casualty("C3", TriageCategory.RED, at=2.0),
        hospitals=hospitals,
    )


def test_fifo_sends_the_first_reported_casualty_first():
    scenario = waiting_when_the_ambulance_is_back((NEAR,))

    assert sent_order(simulate(scenario)) == ["C1", "C3", "C2"]
    assert sent_order(simulate(scenario, priority=fifo)) == ["C1", "C2", "C3"]


def test_the_priority_rule_also_decides_who_gets_the_last_bed():
    scenario = waiting_when_the_ambulance_is_back((Hospital("HOSP-1", "H1", 2),))

    triaged = simulate(scenario)
    first_come = simulate(scenario, priority=fifo)

    assert sent_order(triaged) == ["C1", "C3"]
    assert triaged.unserved == ("C2",)
    assert sent_order(first_come) == ["C1", "C2"]
    assert first_come.unserved == ("C3",)

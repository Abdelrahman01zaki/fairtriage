import pytest

from ai_intelligence_lab.environments.road_network import Junction, Road, RoadNetwork
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.fairness.metrics import fairness_report, gini
from ai_intelligence_lab.fairtriage.simulation.engine import simulate
from ai_intelligence_lab.fairtriage.simulation.scenario import (
    Scenario,
    SimulationResult,
    Transport,
)
from ai_intelligence_lab.fairtriage.simulation.state import WorldState

RED, YELLOW, GREEN, BLACK = (
    TriageCategory.RED,
    TriageCategory.YELLOW,
    TriageCategory.GREEN,
    TriageCategory.BLACK,
)

INCIDENT = Incident(
    "I-1",
    "SCENE",
    (
        Casualty("R1", RED, 0.0),
        Casualty("R2", RED, 0.0),
        Casualty("Y1", YELLOW, 2.0),
        Casualty("G1", GREEN, 0.0),
    ),
)


def make_transport(casualty_id, category, reported, picked_up):
    return Transport(
        casualty_id,
        category,
        "A1",
        "H1",
        reported,
        reported,
        picked_up,
        picked_up + 4.0,
    )


def make_result(transports, unserved):
    state = WorldState.start([Ambulance("A1", "BASE")], [Hospital("H1", "X", 5)])
    return SimulationResult(tuple(transports), tuple(unserved), state, 20.0)


RESULT = make_result(
    [
        make_transport("R1", RED, 0.0, 4.0),
        make_transport("R2", RED, 0.0, 10.0),
        make_transport("Y1", YELLOW, 2.0, 8.0),
    ],
    ["G1"],
)


def test_equal_values_have_no_inequality():
    assert gini([5.0, 5.0, 5.0]) == 0.0


def test_an_empty_list_or_zeros_have_no_inequality():
    assert gini([]) == 0.0
    assert gini([0.0, 0.0, 0.0]) == 0.0


def test_gini_of_known_lists():
    assert gini([0.0, 10.0]) == pytest.approx(0.5)
    assert gini([1.0, 2.0, 3.0, 4.0]) == pytest.approx(0.25)


@pytest.mark.parametrize("bad", [-1.0, float("nan")])
def test_gini_rejects_bad_values(bad):
    with pytest.raises(ValueError):
        gini([1.0, bad])


def test_a_category_reports_its_waits():
    red = fairness_report(INCIDENT, RESULT).category(RED)

    assert red.transported == 2
    assert red.unserved == 0
    assert red.mean_wait == 7.0
    assert red.median_wait == 7.0
    assert red.worst_wait == 10.0
    assert red.gini == pytest.approx(3 / 14)


def test_categories_come_most_urgent_first_and_only_those_present():
    report = fairness_report(INCIDENT, RESULT)

    assert [item.category for item in report.categories] == [RED, YELLOW, GREEN]
    assert report.category(BLACK) is None


def test_unserved_casualties_are_counted_in_their_own_category():
    report = fairness_report(INCIDENT, RESULT)
    green = report.category(GREEN)

    assert green.transported == 0
    assert green.unserved == 1
    assert green.mean_wait is None
    assert green.worst_wait is None
    assert green.gini == 0.0
    assert report.unserved_total == 1


def test_a_transport_of_an_unknown_casualty_is_rejected():
    result = make_result([make_transport("X", RED, 0.0, 3.0)], [])

    with pytest.raises(ValueError):
        fairness_report(INCIDENT, result)


def test_an_unserved_unknown_casualty_is_rejected():
    with pytest.raises(ValueError):
        fairness_report(INCIDENT, make_result([], ["X"]))


def test_a_category_that_disagrees_with_the_incident_is_rejected():
    result = make_result([make_transport("R1", YELLOW, 0.0, 3.0)], [])

    with pytest.raises(ValueError):
        fairness_report(INCIDENT, result)


def test_a_real_run_is_measured_per_category():
    network = RoadNetwork(
        (Junction("A", 0.0, 0.0), Junction("B", 5.0, 0.0)),
        (Road("A", "B", 5.0),),
    )
    incident = Incident(
        "I-2",
        "A",
        (Casualty("C1", RED, 0.0), Casualty("C2", GREEN, 0.0)),
    )
    scenario = Scenario(
        network, incident, (Hospital("H", "B", 5),), (Ambulance("AMB", "B"),)
    )

    report = fairness_report(incident, simulate(scenario))

    assert report.category(RED).worst_wait == 5.0
    assert report.category(GREEN).worst_wait == 15.0
    assert report.unserved_total == 0


def test_a_category_reports_the_time_until_the_hospital():
    red = fairness_report(INCIDENT, RESULT).category(RED)

    assert red.mean_to_hospital == 11.0
    assert red.worst_to_hospital == 14.0


def test_nobody_served_has_no_time_to_hospital():
    green = fairness_report(INCIDENT, RESULT).category(GREEN)

    assert green.mean_to_hospital is None
    assert green.worst_to_hospital is None


def test_a_category_reports_the_fraction_of_its_casualties_served():
    report = fairness_report(INCIDENT, RESULT)

    assert report.category(RED).served_fraction == 1.0
    assert report.category(YELLOW).served_fraction == 1.0
    assert report.category(GREEN).served_fraction == 0.0


def test_a_half_served_category_has_a_fraction_of_one_half():
    incident = Incident(
        "I-3",
        "SCENE",
        (Casualty("R1", RED, 0.0), Casualty("R2", RED, 0.0)),
    )
    result = make_result([make_transport("R1", RED, 0.0, 4.0)], ["R2"])

    assert fairness_report(incident, result).category(RED).served_fraction == 0.5

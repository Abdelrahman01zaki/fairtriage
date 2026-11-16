import pytest

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.validation import validate_allocation
from ai_intelligence_lab.environments.road_network import Junction, Road, RoadNetwork
from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.transport.problem import build_transport_problem

JUNCTIONS = (
    Junction("SCENE", 0.0, 0.0),
    Junction("NEAR", 4.0, 0.0),
    Junction("FAR", 10.0, 0.0),
    Junction("ISLAND", 50.0, 50.0),
)
ROADS = (
    Road("SCENE", "NEAR", 4.0),
    Road("SCENE", "FAR", 10.0),
)
HOSPITALS = (
    Hospital("H-near", "NEAR", 1),
    Hospital("H-far", "FAR", 5, frozenset({"burns"})),
    Hospital("H-island", "ISLAND", 10),
)


def city(roads=ROADS):
    """NEAR is 4 minutes from the scene, FAR is 10, ISLAND has no road."""
    return RoadNetwork(JUNCTIONS, roads)


def incident(*casualties, location="SCENE"):
    return Incident("I-1", location, casualties)


def test_casualties_become_demands_with_their_urgency_and_needs():
    scene = incident(
        Casualty("C-1", TriageCategory.RED, 2.0, needs=["burns"]),
        Casualty("C-2", TriageCategory.GREEN, 0.0),
    )

    first, second = build_transport_problem(city(), scene, HOSPITALS).demands

    assert (first.id, first.priority, first.arrived_at) == ("C-1", 0, 2.0)
    assert first.needs == frozenset({"burns"})
    assert second.priority == TriageCategory.GREEN.urgency


def test_hospitals_become_resources_with_their_beds_and_specialties():
    scene = incident(Casualty("C-1", TriageCategory.RED, 0.0))

    near, far, _island = build_transport_problem(city(), scene, HOSPITALS).resources

    assert (near.id, near.capacity) == ("H-near", 1)
    assert far.offers == frozenset({"burns"})


def test_the_cost_is_the_driving_time_from_the_scene_for_every_casualty():
    scene = incident(
        Casualty("C-1", TriageCategory.RED, 0.0),
        Casualty("C-2", TriageCategory.GREEN, 0.0),
    )

    problem = build_transport_problem(city(), scene, HOSPITALS)

    for casualty in ("C-1", "C-2"):
        assert problem.cost_of(casualty, "H-near") == pytest.approx(4.0)
        assert problem.cost_of(casualty, "H-far") == pytest.approx(10.0)


def test_a_hospital_with_no_route_gets_no_cost():
    scene = incident(Casualty("C-1", TriageCategory.RED, 0.0))

    problem = build_transport_problem(city(), scene, HOSPITALS)

    assert problem.cost_of("C-1", "H-island") is None


def test_a_closed_road_removes_the_hospital_behind_it():
    scene = incident(Casualty("C-1", TriageCategory.RED, 0.0))
    closed = city().without_road("SCENE", "NEAR")

    problem = build_transport_problem(closed, scene, HOSPITALS)

    assert problem.cost_of("C-1", "H-near") is None
    assert problem.cost_of("C-1", "H-far") == pytest.approx(10.0)


def test_the_route_is_driven_from_the_scene_to_the_hospital():
    scene = incident(Casualty("C-1", TriageCategory.RED, 0.0))
    roads = (Road("NEAR", "SCENE", 4.0, two_way=False), Road("SCENE", "FAR", 10.0))

    problem = build_transport_problem(city(roads), scene, HOSPITALS)

    assert problem.cost_of("C-1", "H-near") is None


def test_the_most_urgent_casualty_gets_the_nearest_bed():
    scene = incident(
        Casualty("green", TriageCategory.GREEN, 0.0),
        Casualty("yellow", TriageCategory.YELLOW, 0.0),
        Casualty("red", TriageCategory.RED, 0.0),
    )
    problem = build_transport_problem(city(), scene, HOSPITALS)

    allocation = greedy_allocate(problem)

    validate_allocation(problem, allocation)
    assert allocation.placement_of("red").resource_id == "H-near"
    assert allocation.placement_of("yellow").resource_id == "H-far"
    assert allocation.placement_of("green").resource_id == "H-far"
    assert allocation.unplaced == ()


def test_a_casualty_needing_a_specialty_goes_to_a_hospital_that_has_it():
    scene = incident(
        Casualty("burnt", TriageCategory.RED, 0.0, needs=["burns"]),
        Casualty("minor", TriageCategory.GREEN, 0.0),
    )
    problem = build_transport_problem(city(), scene, HOSPITALS)

    allocation = greedy_allocate(problem)

    assert allocation.placement_of("burnt").resource_id == "H-far"
    assert allocation.placement_of("minor").resource_id == "H-near"


def test_in_the_same_category_the_longest_waiting_casualty_goes_first():
    scene = incident(
        Casualty("late", TriageCategory.RED, 5.0),
        Casualty("early", TriageCategory.RED, 1.0),
    )
    problem = build_transport_problem(city(), scene, HOSPITALS)

    allocation = greedy_allocate(problem)

    assert allocation.placement_of("early").resource_id == "H-near"
    assert allocation.placement_of("late").resource_id == "H-far"


def test_an_incident_with_no_hospitals_is_rejected():
    scene = incident(Casualty("C-1", TriageCategory.RED, 0.0))

    with pytest.raises(ValueError):
        build_transport_problem(city(), scene, ())


def test_a_scene_that_is_not_on_the_network_is_rejected():
    scene = incident(Casualty("C-1", TriageCategory.RED, 0.0), location="NOWHERE")

    with pytest.raises(ValueError):
        build_transport_problem(city(), scene, HOSPITALS)

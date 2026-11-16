import pytest

from ai_intelligence_lab.environments.road_network import Junction, Road, RoadNetwork
from ai_intelligence_lab.fairtriage.dispatch.dispatcher import (
    Dispatch,
    arrival_options,
    nearest_ambulance,
)
from ai_intelligence_lab.fairtriage.dispatch.routing import Route
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance

JUNCTIONS = (
    Junction("NORTH", 0.0, 0.0),
    Junction("SCENE", 4.0, 0.0),
    Junction("EAST", 10.0, 0.0),
    Junction("ISLAND", 30.0, 30.0),
)
ROADS = (
    Road("NORTH", "SCENE", 4.0),
    Road("EAST", "SCENE", 3.0),
)


def city(roads=ROADS):
    """NORTH is 4 minutes from the scene, EAST is 3, ISLAND has no road."""
    return RoadNetwork(JUNCTIONS, roads)


def test_the_ambulance_that_arrives_first_is_chosen():
    fleet = (Ambulance("A-1", "NORTH"), Ambulance("A-2", "EAST"))

    chosen = nearest_ambulance(city(), fleet, "SCENE")

    assert chosen is not None
    assert chosen.ambulance.id == "A-2"
    assert chosen.route.path == ("EAST", "SCENE")
    assert chosen.minutes == pytest.approx(3.0)


def test_an_ambulance_already_at_the_scene_arrives_in_no_time():
    fleet = (Ambulance("A-1", "NORTH"), Ambulance("A-3", "SCENE"))

    chosen = nearest_ambulance(city(), fleet, "SCENE")

    assert chosen is not None
    assert chosen.ambulance.id == "A-3"
    assert chosen.minutes == 0.0


def test_an_ambulance_that_cannot_reach_the_scene_is_skipped():
    fleet = (Ambulance("A-1", "NORTH"), Ambulance("A-4", "ISLAND"))

    options = arrival_options(city(), fleet, "SCENE")

    assert [option.ambulance.id for option in options] == ["A-1"]


def test_no_ambulance_can_reach_the_scene_gives_none():
    fleet = (Ambulance("A-4", "ISLAND"),)

    assert nearest_ambulance(city(), fleet, "SCENE") is None


def test_an_empty_fleet_gives_nothing():
    assert arrival_options(city(), (), "SCENE") == ()
    assert nearest_ambulance(city(), (), "SCENE") is None


def test_equal_times_are_broken_by_ambulance_id():
    fleet = (Ambulance("A-2", "NORTH"), Ambulance("A-1", "NORTH"))

    chosen = nearest_ambulance(city(), fleet, "SCENE")

    assert chosen is not None
    assert chosen.ambulance.id == "A-1"


def test_options_are_listed_fastest_first():
    fleet = (
        Ambulance("A-1", "NORTH"),
        Ambulance("A-2", "EAST"),
        Ambulance("A-3", "SCENE"),
    )

    options = arrival_options(city(), fleet, "SCENE")

    assert [option.ambulance.id for option in options] == ["A-3", "A-2", "A-1"]
    assert [option.minutes for option in options] == sorted(
        option.minutes for option in options
    )


def test_a_closed_road_changes_which_ambulance_is_chosen():
    fleet = (Ambulance("A-1", "NORTH"), Ambulance("A-2", "EAST"))
    closed = city().without_road("EAST", "SCENE")

    chosen = nearest_ambulance(closed, fleet, "SCENE")

    assert chosen is not None
    assert chosen.ambulance.id == "A-1"
    assert chosen.minutes == pytest.approx(4.0)


def test_one_way_roads_are_followed_from_the_base_to_the_scene():
    roads = (
        Road("NORTH", "SCENE", 4.0),
        Road("SCENE", "EAST", 1.0, two_way=False),
    )
    fleet = (Ambulance("A-1", "NORTH"), Ambulance("A-2", "EAST"))

    options = arrival_options(city(roads), fleet, "SCENE")

    assert [option.ambulance.id for option in options] == ["A-1"]


def test_duplicate_ambulance_ids_are_rejected():
    fleet = (Ambulance("A-1", "NORTH"), Ambulance("A-1", "EAST"))

    with pytest.raises(ValueError):
        arrival_options(city(), fleet, "SCENE")


def test_an_unknown_base_is_rejected():
    fleet = (Ambulance("A-9", "NOWHERE"),)

    with pytest.raises(ValueError):
        nearest_ambulance(city(), fleet, "SCENE")


def test_an_unknown_scene_is_rejected():
    fleet = (Ambulance("A-1", "NORTH"),)

    with pytest.raises(ValueError):
        nearest_ambulance(city(), fleet, "NOWHERE")


def test_a_dispatch_route_must_start_at_the_ambulance_base():
    with pytest.raises(ValueError):
        Dispatch(Ambulance("A-1", "NORTH"), Route(("EAST", "SCENE"), 3.0))


def test_a_dispatch_reports_the_time_of_its_route():
    dispatch = Dispatch(Ambulance("A-1", "NORTH"), Route(("NORTH", "SCENE"), 4.0))

    assert dispatch.minutes == 4.0

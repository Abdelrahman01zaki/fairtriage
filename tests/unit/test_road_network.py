import dataclasses
import math

import pytest

from ai_intelligence_lab.environments.road_network import (
    Junction,
    Road,
    RoadNetwork,
)


def make_network(**overrides):
    parts = {
        "junctions": (
            Junction("A", 0.0, 0.0),
            Junction("B", 3.0, 4.0),
            Junction("C", 6.0, 8.0),
        ),
        "roads": (Road("A", "B", 5.0), Road("B", "C", 4.0)),
    }
    parts.update(overrides)
    return RoadNetwork(**parts)


# --- Junction -----------------------------------------------------------


def test_junction_keeps_its_fields():
    item = Junction("A", 1.5, -2.0)

    assert (item.id, item.x, item.y) == ("A", 1.5, -2.0)


def test_junction_needs_an_id():
    with pytest.raises(ValueError):
        Junction("", 0.0, 0.0)


@pytest.mark.parametrize(("x", "y"), [(math.nan, 0.0), (0.0, math.inf)])
def test_junction_position_must_be_finite(x, y):
    with pytest.raises(ValueError):
        Junction("A", x, y)


# --- Road ---------------------------------------------------------------


def test_road_is_two_way_by_default():
    item = Road("A", "B", 5.0)

    assert (item.source, item.target, item.minutes) == ("A", "B", 5.0)
    assert item.two_way is True


def test_road_needs_both_ends():
    with pytest.raises(ValueError):
        Road("", "B", 5.0)
    with pytest.raises(ValueError):
        Road("A", "", 5.0)


def test_road_cannot_loop_back_to_the_same_junction():
    with pytest.raises(ValueError):
        Road("A", "A", 5.0)


@pytest.mark.parametrize("bad_minutes", [0.0, -1.0, math.nan, math.inf])
def test_road_time_must_be_positive_and_finite(bad_minutes):
    with pytest.raises(ValueError):
        Road("A", "B", bad_minutes)


# --- RoadNetwork --------------------------------------------------------


def test_network_keeps_its_parts_in_order():
    network = make_network()

    assert [j.id for j in network.junctions] == ["A", "B", "C"]
    assert [(r.source, r.target) for r in network.roads] == [("A", "B"), ("B", "C")]


def test_neighbors_follow_the_order_roads_were_declared():
    network = make_network(roads=(Road("A", "C", 9.0), Road("A", "B", 5.0)))

    assert network.neighbors("A") == ("C", "B")


def test_a_two_way_road_can_be_driven_both_ways():
    network = make_network()

    assert network.neighbors("B") == ("A", "C")
    assert network.travel_minutes("B", "A") == 5.0


def test_a_one_way_road_can_only_be_driven_one_way():
    network = make_network(roads=(Road("A", "B", 5.0, two_way=False),))

    assert network.neighbors("A") == ("B",)
    assert network.neighbors("B") == ()
    with pytest.raises(ValueError):
        network.travel_minutes("B", "A")


def test_travel_minutes_is_the_time_of_that_road():
    assert make_network().travel_minutes("B", "C") == 4.0


def test_travel_minutes_rejects_a_missing_road():
    with pytest.raises(ValueError):
        make_network().travel_minutes("A", "C")


def test_network_needs_at_least_one_junction():
    with pytest.raises(ValueError):
        make_network(junctions=(), roads=())


def test_duplicate_junction_ids_are_rejected():
    with pytest.raises(ValueError):
        make_network(junctions=(Junction("A", 0.0, 0.0), Junction("A", 1.0, 1.0)))


def test_a_road_to_an_unknown_junction_is_rejected():
    # Almost always a typo in a junction name.
    with pytest.raises(ValueError):
        make_network(roads=(Road("A", "Z", 5.0),))


def test_two_roads_in_the_same_direction_are_rejected():
    with pytest.raises(ValueError):
        make_network(roads=(Road("A", "B", 5.0), Road("A", "B", 7.0)))


def test_opposite_one_way_roads_may_take_different_times():
    network = make_network(
        roads=(
            Road("A", "B", 5.0, two_way=False),
            Road("B", "A", 7.0, two_way=False),
        )
    )

    assert network.travel_minutes("A", "B") == 5.0
    assert network.travel_minutes("B", "A") == 7.0


def test_neighbors_of_an_unknown_junction_are_rejected():
    with pytest.raises(ValueError):
        make_network().neighbors("Z")


def test_distance_is_the_straight_line_between_junctions():
    assert make_network().distance("A", "B") == 5.0


def test_without_road_removes_the_road_in_both_directions():
    closed = make_network().without_road("A", "B")

    assert closed.neighbors("A") == ()
    assert closed.neighbors("B") == ("C",)


def test_without_road_leaves_the_original_network_unchanged():
    network = make_network()

    network.without_road("A", "B")

    assert network.neighbors("A") == ("B",)


def test_without_road_rejects_a_pair_with_no_road():
    with pytest.raises(ValueError):
        make_network().without_road("A", "C")


def test_network_is_immutable():
    network = make_network()

    with pytest.raises(dataclasses.FrozenInstanceError):
        network.roads = ()

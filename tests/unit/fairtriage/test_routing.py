import heapq
import math
import random

import pytest

from ai_intelligence_lab.core.events import EventType
from ai_intelligence_lab.environments.road_network import (
    Junction,
    Road,
    RoadNetwork,
)
from ai_intelligence_lab.fairtriage.dispatch.routing import (
    Route,
    find_route,
    route_events,
)

JUNCTIONS = (
    Junction("A", 0.0, 0.0),
    Junction("B", 4.0, 0.0),
    Junction("C", 8.0, 0.0),
    Junction("D", 4.0, 3.0),
)


def diamond(**overrides):
    """A to C: 8 minutes through B, 10 through D, or 20 on the direct road."""
    parts = {
        "junctions": JUNCTIONS,
        "roads": (
            Road("A", "B", 4.0),
            Road("B", "C", 4.0),
            Road("A", "D", 5.0),
            Road("D", "C", 5.0),
            Road("A", "C", 20.0),
        ),
    }
    parts.update(overrides)
    return RoadNetwork(**parts)


def lattice(size=4, seed=1):
    """A square lattice of roads with random times, for comparing with Dijkstra."""
    rng = random.Random(seed)
    junctions = tuple(
        Junction(f"{r}{c}", float(c), float(r))
        for r in range(size)
        for c in range(size)
    )
    roads = []
    for r in range(size):
        for c in range(size):
            if c + 1 < size:
                roads.append(Road(f"{r}{c}", f"{r}{c + 1}", rng.uniform(0.5, 3.0)))
            if r + 1 < size:
                roads.append(Road(f"{r}{c}", f"{r + 1}{c}", rng.uniform(0.5, 3.0)))
    return RoadNetwork(junctions, tuple(roads))


def dijkstra(network, source, target):
    """Reference answer, written without any heuristic."""
    best = {source: 0.0}
    queue = [(0.0, source)]
    while queue:
        cost, node = heapq.heappop(queue)
        if node == target:
            return cost
        if cost > best[node]:
            continue
        for following in network.neighbors(node):
            new_cost = cost + network.travel_minutes(node, following)
            if new_cost < best.get(following, math.inf):
                best[following] = new_cost
                heapq.heappush(queue, (new_cost, following))
    return None


# --- Route --------------------------------------------------------------


def test_route_knows_where_it_starts_and_ends():
    route = Route(("A", "B", "C"), 8.0)

    assert route.source == "A"
    assert route.target == "C"


def test_route_needs_at_least_one_junction():
    with pytest.raises(ValueError):
        Route((), 1.0)


@pytest.mark.parametrize("bad_minutes", [-1.0, math.nan])
def test_route_time_must_be_a_real_number_of_zero_or_more(bad_minutes):
    with pytest.raises(ValueError):
        Route(("A",), bad_minutes)


# --- find_route ---------------------------------------------------------


def test_the_fastest_route_is_chosen_not_the_one_with_fewest_roads():
    route = find_route(diamond(), "A", "C")

    assert route == Route(("A", "B", "C"), 8.0)


def test_a_route_from_a_junction_to_itself_takes_no_time():
    assert find_route(diamond(), "A", "A") == Route(("A",), 0.0)


def test_an_unreachable_junction_gives_no_route():
    network = diamond(junctions=(*JUNCTIONS, Junction("E", 20.0, 0.0)))

    assert find_route(network, "A", "E") is None


@pytest.mark.parametrize(("source", "target"), [("Z", "A"), ("A", "Z")])
def test_an_unknown_junction_is_rejected(source, target):
    with pytest.raises(ValueError):
        find_route(diamond(), source, target)


def test_a_closed_road_sends_the_route_the_other_way_round():
    closed = diamond().without_road("B", "C")

    assert find_route(closed, "A", "C") == Route(("A", "D", "C"), 10.0)


def test_one_way_roads_are_respected():
    network = diamond(roads=(Road("A", "B", 4.0, two_way=False),))

    assert find_route(network, "A", "B") == Route(("A", "B"), 4.0)
    assert find_route(network, "B", "A") is None


def test_junctions_at_the_same_place_still_have_a_route():
    network = RoadNetwork(
        (Junction("X", 0.0, 0.0), Junction("Y", 0.0, 0.0)),
        (Road("X", "Y", 3.0),),
    )

    assert find_route(network, "X", "Y") == Route(("X", "Y"), 3.0)


def test_route_events_run_from_started_to_completed():
    kinds = [event.kind for event in route_events(diamond(), "A", "C")]

    assert kinds[0] is EventType.STARTED
    assert kinds[-1] is EventType.COMPLETED
    assert EventType.PATH_FOUND in kinds


def test_astar_finds_the_same_time_as_plain_dijkstra_between_every_pair():
    network = lattice()
    names = [junction.id for junction in network.junctions]

    for source in names:
        for target in names:
            route = find_route(network, source, target)

            assert route is not None
            assert route.minutes == pytest.approx(dijkstra(network, source, target))

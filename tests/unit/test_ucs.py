from itertools import pairwise

from ai_intelligence_lab.algorithms.search.ucs import ucs
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid


def found_path(events):
    paths = [e.path for e in events if e.kind is EventType.PATH_FOUND]
    return paths[0] if paths else None


def found_cost(events):
    costs = [e.cost for e in events if e.kind is EventType.PATH_FOUND]
    return costs[0] if costs else None


def test_exact_event_sequence_with_an_expensive_cell():
    # (0, 1) costs 10 to enter, so the cheap route goes the long way
    # around through row 1 instead of straight across row 0.
    grid = Grid.from_text(["S.G", "..."], weights={(0, 1): 10.0})

    events = list(ucs(grid))

    assert events == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0), cost=0.0),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0), cost=0.0),
        AlgorithmEvent(
            EventType.NODE_DISCOVERED, node=(0, 1), parent=(0, 0), cost=10.0
        ),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(1, 0), parent=(0, 0), cost=1.0),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(1, 0), cost=1.0),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(1, 1), parent=(1, 0), cost=2.0),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(1, 1), cost=2.0),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(1, 2), parent=(1, 1), cost=3.0),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(1, 2), cost=3.0),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 2), parent=(1, 2), cost=4.0),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 2), cost=4.0),
        AlgorithmEvent(
            EventType.PATH_FOUND,
            node=(0, 2),
            path=((0, 0), (1, 0), (1, 1), (1, 2), (0, 2)),
            cost=4.0,
        ),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_cheap_detour_beats_expensive_shortcut():
    grid = Grid.from_text(["S.G", "..."], weights={(0, 1): 10.0})

    events = list(ucs(grid))

    # Straight across row 0 would cost 0 + 10 (enter (0,1)) + 1 (enter
    # goal) = 11. UCS must prefer the 4-cost detour through row 1.
    assert found_cost(events) == 4.0
    assert found_cost(events) < 11.0


def test_on_a_uniform_grid_cost_equals_path_length():
    grid = Grid.from_text(["S...", "....", "...G"])

    events = list(ucs(grid))
    path = found_path(events)

    assert found_cost(events) == len(path) - 1


def test_no_path_when_goal_is_walled_off():
    events = list(ucs(Grid.from_text(["S#G"])))

    assert found_path(events) is None
    assert [e.kind for e in events] == [
        EventType.STARTED,
        EventType.NODE_EXPANDED,
        EventType.COMPLETED,
    ]


def test_start_equal_to_goal():
    grid = Grid(1, 1, start=(0, 0), goal=(0, 0))

    events = list(ucs(grid))

    assert events == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0), cost=0.0),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0), cost=0.0),
        AlgorithmEvent(EventType.PATH_FOUND, node=(0, 0), path=((0, 0),), cost=0.0),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_generator_is_lazy():
    generator = ucs(Grid.from_text(["S.G"]))
    assert next(generator).kind is EventType.STARTED
    assert next(generator).kind is EventType.NODE_EXPANDED


def test_same_grid_gives_same_events():
    grid = Grid.from_text(["S.#.", "..#.", "...G"])
    assert list(ucs(grid)) == list(ucs(grid))


def test_node_updated_never_fires_with_per_cell_costs():
    # Cost here depends only on the cell being entered, not on which
    # neighbour you came from. So the predecessor with the smallest g(n)
    # is always expanded first (UCS invariant) and therefore always
    # offers the cheapest route to any shared neighbour first. No later,
    # more-expensive predecessor can ever beat it, so NODE_UPDATED is
    # mathematically unreachable under this cost model, on any grid.
    grids = [
        Grid.from_text(["S.G", "..."], weights={(0, 1): 1.0, (1, 0): 1.0}),
        Grid.from_text(["S...", "....", "....", "...G"]),
        Grid.from_text(
            ["S....", ".....", ".....", "....G"],
            weights={(0, 1): 3.0, (1, 0): 7.0, (2, 2): 4.0},
        ),
    ]

    for grid in grids:
        kinds = [e.kind for e in ucs(grid)]
        assert EventType.NODE_UPDATED not in kinds


_BIG_GRID_ROWS = ["S..#.", ".#...", "...#G"]
_BIG_GRID_WEIGHTS = {(0, 1): 3.0, (1, 0): 2.0, (2, 2): 5.0, (1, 3): 4.0}


def _big_grid():
    return Grid.from_text(_BIG_GRID_ROWS, weights=_BIG_GRID_WEIGHTS)


def test_expanded_costs_never_decrease():
    events = list(ucs(_big_grid()))

    costs = [e.cost for e in events if e.kind is EventType.NODE_EXPANDED]

    assert costs == sorted(costs)


def test_every_cell_is_expanded_at_most_once():
    events = list(ucs(_big_grid()))

    expanded = [e.node for e in events if e.kind is EventType.NODE_EXPANDED]

    assert len(expanded) == len(set(expanded))


def test_reported_cost_equals_sum_of_entering_costs_along_the_path():
    grid = _big_grid()
    events = list(ucs(grid))
    path = found_path(events)

    assert path is not None
    assert abs(found_cost(events) - sum(grid.cost(c) for c in path[1:])) < 1e-9


def test_path_is_connected_from_start_to_goal():
    grid = _big_grid()
    path = found_path(list(ucs(grid)))

    assert path[0] == grid.start
    assert path[-1] == grid.goal
    for a, b in pairwise(path):
        assert b in grid.neighbors(a)


def test_fractional_weights_are_summed_exactly_enough():
    grid = Grid.from_text(["S.G"], weights={(0, 1): 0.1, (0, 2): 0.2})

    assert abs(found_cost(list(ucs(grid))) - 0.3) < 1e-9


def test_forced_expensive_cell_is_paid_when_there_is_no_other_route():
    grid = Grid.from_text(["S#G", "..."], weights={(1, 1): 7.0})

    assert found_cost(list(ucs(grid))) == 10.0

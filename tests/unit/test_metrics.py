from ai_intelligence_lab.algorithms.search.bfs import bfs
from ai_intelligence_lab.algorithms.search.greedy import greedy
from ai_intelligence_lab.algorithms.search.ucs import ucs
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid
from ai_intelligence_lab.evaluation.metrics import measure


def _weighted_grid():
    return Grid.from_text(["S.G", "..."], weights={(0, 1): 10.0})


def test_ucs_counts_on_weighted_grid():
    grid = _weighted_grid()

    m = measure(grid, ucs(grid))

    assert m.events == 13
    assert m.expanded == 5
    assert m.discovered == 5
    assert m.updated == 0
    assert m.found
    assert m.path_cost == 4.0


def test_bfs_pays_the_expensive_cell_it_cannot_see():
    grid = _weighted_grid()

    m = measure(grid, bfs(grid))

    assert m.events == 11
    assert m.expanded == 4
    assert m.discovered == 4
    assert m.path == ((0, 0), (0, 1), (0, 2))
    assert m.path_cost == 11.0


def test_greedy_counts_and_real_path_cost():
    grid = _weighted_grid()

    m = measure(grid, greedy(grid))

    assert m.events == 10
    assert m.expanded == 3
    assert m.path_cost == 11.0


def test_no_path_means_not_found():
    grid = Grid.from_text(["S#G"])

    m = measure(grid, bfs(grid))

    assert not m.found
    assert m.path is None
    assert m.path_cost is None


def test_start_equal_to_goal_costs_zero():
    grid = Grid(1, 1, start=(0, 0), goal=(0, 0))

    m = measure(grid, ucs(grid))

    assert m.path == ((0, 0),)
    assert m.path_cost == 0.0


def test_updated_events_are_counted():
    grid = Grid.from_text(["S.G"])
    events = [
        AlgorithmEvent(EventType.STARTED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 1), parent=(0, 0)),
        AlgorithmEvent(EventType.NODE_UPDATED, node=(0, 1), parent=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 1)),
        AlgorithmEvent(EventType.COMPLETED),
    ]

    m = measure(grid, events)

    assert (m.events, m.discovered, m.updated, m.expanded) == (5, 1, 1, 1)


def test_seconds_is_not_negative():
    grid = _weighted_grid()

    assert measure(grid, ucs(grid)).seconds >= 0.0

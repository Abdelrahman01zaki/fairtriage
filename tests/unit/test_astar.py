import pytest

from ai_intelligence_lab.algorithms.search.astar import astar
from ai_intelligence_lab.algorithms.search.ucs import ucs
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid


def _found_cost(events):
    return [e.cost for e in events if e.kind is EventType.PATH_FOUND][0]


def _expanded_count(events):
    return sum(1 for e in events if e.kind is EventType.NODE_EXPANDED)


def test_astar_event_sequence_on_weighted_grid():
    grid = Grid.from_text(["S.G", "..."], weights={(0, 1): 10.0})

    assert list(astar(grid)) == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0), cost=0.0),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0), cost=0.0),
        AlgorithmEvent(
            EventType.NODE_DISCOVERED, node=(0, 1), parent=(0, 0), cost=10.0
        ),
        AlgorithmEvent(
            EventType.NODE_DISCOVERED, node=(1, 0), parent=(0, 0), cost=1.0
        ),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(1, 0), cost=1.0),
        AlgorithmEvent(
            EventType.NODE_DISCOVERED, node=(1, 1), parent=(1, 0), cost=2.0
        ),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(1, 1), cost=2.0),
        AlgorithmEvent(
            EventType.NODE_DISCOVERED, node=(1, 2), parent=(1, 1), cost=3.0
        ),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(1, 2), cost=3.0),
        AlgorithmEvent(
            EventType.NODE_DISCOVERED, node=(0, 2), parent=(1, 2), cost=4.0
        ),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 2), cost=4.0),
        AlgorithmEvent(
            EventType.PATH_FOUND,
            node=(0, 2),
            path=((0, 0), (1, 0), (1, 1), (1, 2), (0, 2)),
            cost=4.0,
        ),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_astar_finds_the_same_cost_as_ucs():
    grid = Grid.from_text(["S.G", "..."], weights={(0, 1): 10.0})

    assert _found_cost(astar(grid)) == _found_cost(ucs(grid)) == 4.0


def test_astar_stays_optimal_when_some_cells_cost_less_than_default():
    grid = Grid.from_text(
        ["S.G", "..."],
        weights={(1, 0): 0.1, (1, 1): 0.1, (1, 2): 0.1},
    )

    assert _found_cost(astar(grid)) == pytest.approx(1.3)
    assert _found_cost(astar(grid)) == pytest.approx(_found_cost(ucs(grid)))


def test_astar_expands_fewer_cells_than_ucs_on_an_open_grid():
    grid = Grid.from_text(
        [".....", ".....", "S.G..", ".....", "....."]
    )

    astar_expanded = _expanded_count(astar(grid))
    ucs_expanded = _expanded_count(ucs(grid))

    assert astar_expanded == 3
    assert astar_expanded < ucs_expanded


def test_start_equal_to_goal_finds_trivial_path():
    grid = Grid(1, 1, start=(0, 0), goal=(0, 0))

    assert list(astar(grid)) == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0), cost=0.0),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0), cost=0.0),
        AlgorithmEvent(
            EventType.PATH_FOUND, node=(0, 0), path=((0, 0),), cost=0.0
        ),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_unreachable_goal_ends_without_path():
    grid = Grid.from_text(["S#G"])

    kinds = [e.kind for e in astar(grid)]

    assert kinds == [
        EventType.STARTED,
        EventType.NODE_EXPANDED,
        EventType.COMPLETED,
    ]


def test_astar_is_lazy():
    generator = astar(Grid.from_text(["S.G"]))

    assert next(generator).kind is EventType.STARTED
    assert next(generator).kind is EventType.NODE_EXPANDED

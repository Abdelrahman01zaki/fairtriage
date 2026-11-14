from ai_intelligence_lab.algorithms.search.greedy import greedy
from ai_intelligence_lab.algorithms.search.ucs import ucs
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid


def _found_cost(events):
    costs = [e.cost for e in events if e.kind is EventType.PATH_FOUND]
    return costs[0]


def test_greedy_event_sequence_on_weighted_grid():
    grid = Grid.from_text(["S.G", "..."], weights={(0, 1): 10.0})

    assert list(greedy(grid)) == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 1), parent=(0, 0)),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(1, 0), parent=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 1)),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 2), parent=(0, 1)),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(1, 1), parent=(0, 1)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 2)),
        AlgorithmEvent(
            EventType.PATH_FOUND,
            node=(0, 2),
            path=((0, 0), (0, 1), (0, 2)),
            cost=11.0,
        ),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_greedy_path_can_cost_more_than_ucs_path():
    grid = Grid.from_text(["S.G", "..."], weights={(0, 1): 10.0})

    assert _found_cost(greedy(grid)) == 11.0
    assert _found_cost(ucs(grid)) == 4.0


def test_start_equal_to_goal_finds_trivial_path():
    grid = Grid(1, 1, start=(0, 0), goal=(0, 0))

    assert list(greedy(grid)) == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0)),
        AlgorithmEvent(
            EventType.PATH_FOUND, node=(0, 0), path=((0, 0),), cost=0.0
        ),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_unreachable_goal_ends_without_path():
    grid = Grid.from_text(["S#G"])

    kinds = [e.kind for e in greedy(grid)]

    assert kinds == [
        EventType.STARTED,
        EventType.NODE_EXPANDED,
        EventType.COMPLETED,
    ]


def test_no_cell_is_discovered_twice():
    grid = Grid.from_text(["S...", "....", "...G"])

    discovered = [
        e.node for e in greedy(grid) if e.kind is EventType.NODE_DISCOVERED
    ]

    assert len(discovered) == len(set(discovered))


def test_greedy_is_lazy():
    generator = greedy(Grid.from_text(["S.G"]))

    assert next(generator).kind is EventType.STARTED
    assert next(generator).kind is EventType.NODE_EXPANDED

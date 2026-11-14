from itertools import pairwise

from ai_intelligence_lab.algorithms.search.bfs import bfs
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid


def kinds(events):
    return [event.kind for event in events]


def found_path(events):
    paths = [e.path for e in events if e.kind is EventType.PATH_FOUND]
    return paths[0] if paths else None


def test_exact_event_sequence_on_corridor():
    events = list(bfs(Grid.from_text(["S.G"])))

    assert events == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 1), parent=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 1)),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 2), parent=(0, 1)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 2)),
        AlgorithmEvent(
            EventType.PATH_FOUND,
            node=(0, 2),
            path=((0, 0), (0, 1), (0, 2)),
        ),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_path_goes_around_wall_with_fixed_tie_break():
    grid = Grid.from_text(["S.#.", "..#.", "...G"])

    path = found_path(list(bfs(grid)))

    assert path == ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (2, 3))


def test_path_in_open_grid_is_shortest_and_valid():
    grid = Grid.from_text(["S....", ".....", ".....", ".....", "....G"])

    path = found_path(list(bfs(grid)))

    assert path[0] == grid.start
    assert path[-1] == grid.goal
    assert len(path) == 9  # 8 moves = Manhattan distance
    assert all(grid.is_walkable(cell) for cell in path)

    for (r1, c1), (r2, c2) in pairwise(path):
        assert abs(r1 - r2) + abs(c1 - c2) == 1


def test_no_path_when_goal_is_walled_off():
    events = list(bfs(Grid.from_text(["S#G"])))

    assert found_path(events) is None
    assert kinds(events) == [
        EventType.STARTED,
        EventType.NODE_EXPANDED,
        EventType.COMPLETED,
    ]


def test_start_equal_to_goal():
    grid = Grid(1, 1, start=(0, 0), goal=(0, 0))

    events = list(bfs(grid))

    assert events == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0)),
        AlgorithmEvent(EventType.PATH_FOUND, node=(0, 0), path=((0, 0),)),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_events_obey_ordering_rules():
    grid = Grid.from_text(["S..", "...", "..G"])
    events = list(bfs(grid))

    assert events[0].kind is EventType.STARTED
    assert events[-1].kind is EventType.COMPLETED

    discovered = []
    expanded = set()

    for event in events:
        if event.kind is EventType.NODE_DISCOVERED:
            assert event.parent in expanded  # parent was expanded first
            discovered.append(event.node)
        elif event.kind is EventType.NODE_EXPANDED:
            expanded.add(event.node)

    assert len(discovered) == len(set(discovered))  # never twice


def test_generator_is_lazy():
    generator = bfs(Grid.from_text(["S.G"]))

    assert next(generator).kind is EventType.STARTED
    assert next(generator).kind is EventType.NODE_EXPANDED


def test_same_grid_gives_same_events():
    grid = Grid.from_text(["S.#.", "..#.", "...G"])

    assert list(bfs(grid)) == list(bfs(grid))

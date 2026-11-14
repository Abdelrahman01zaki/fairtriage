from ai_intelligence_lab.algorithms.search.bfs import bfs
from ai_intelligence_lab.algorithms.search.dfs import dfs
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid


def found_path(events):
    paths = [e.path for e in events if e.kind is EventType.PATH_FOUND]
    return paths[0] if paths else None


def test_exact_event_sequence_on_corridor():
    events = list(dfs(Grid.from_text(["S.G"])))

    assert events == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 1), parent=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 1)),
        AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 2), parent=(0, 1)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 2)),
        AlgorithmEvent(
            EventType.PATH_FOUND, node=(0, 2), path=((0, 0), (0, 1), (0, 2))
        ),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_path_is_valid_but_not_shortest():
    grid = Grid.from_text(["S..", "G.."])

    bfs_path = found_path(list(bfs(grid)))
    dfs_path = found_path(list(dfs(grid)))

    assert bfs_path == ((0, 0), (1, 0))
    assert dfs_path == ((0, 0), (0, 1), (0, 2), (1, 2), (1, 1), (1, 0))


def test_a_cell_can_be_discovered_again_before_it_is_expanded():
    events = list(dfs(Grid.from_text(["S..", "G.."])))

    parents_seen = [
        e.parent
        for e in events
        if e.kind is EventType.NODE_DISCOVERED and e.node == (1, 1)
    ]

    assert parents_seen == [(0, 1), (1, 2)]


def test_no_path_when_goal_is_walled_off():
    events = list(dfs(Grid.from_text(["S#G"])))

    assert found_path(events) is None
    assert [e.kind for e in events] == [
        EventType.STARTED,
        EventType.NODE_EXPANDED,
        EventType.COMPLETED,
    ]


def test_start_equal_to_goal():
    grid = Grid(1, 1, start=(0, 0), goal=(0, 0))

    events = list(dfs(grid))

    assert events == [
        AlgorithmEvent(EventType.STARTED, node=(0, 0)),
        AlgorithmEvent(EventType.NODE_EXPANDED, node=(0, 0)),
        AlgorithmEvent(EventType.PATH_FOUND, node=(0, 0), path=((0, 0),)),
        AlgorithmEvent(EventType.COMPLETED),
    ]


def test_events_obey_ordering_rules():
    grid = Grid.from_text(["S..", "...", "..G"])
    events = list(dfs(grid))

    assert events[0].kind is EventType.STARTED
    assert events[-1].kind is EventType.COMPLETED

    discovered, expanded = set(), set()
    for event in events:
        if event.kind is EventType.NODE_DISCOVERED:
            assert event.parent in expanded
            discovered.add(event.node)
        elif event.kind is EventType.NODE_EXPANDED:
            assert event.node not in expanded
            assert event.node == grid.start or event.node in discovered
            expanded.add(event.node)


def test_generator_is_lazy():
    generator = dfs(Grid.from_text(["S.G"]))
    assert next(generator).kind is EventType.STARTED
    assert next(generator).kind is EventType.NODE_EXPANDED


def test_same_grid_gives_same_events():
    grid = Grid.from_text(["S.#.", "..#.", "...G"])
    assert list(dfs(grid)) == list(dfs(grid))

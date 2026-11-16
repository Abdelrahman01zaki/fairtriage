from ai_intelligence_lab.algorithms.search.best_first import best_first
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid


class Graph:
    """A tiny search space whose cost depends on the move, not on the target."""

    def __init__(self, start, goal, edges):
        self.start = start
        self.goal = goal
        self._edges = edges

    def neighbors(self, node):
        return tuple(target for (source, target) in self._edges if source == node)

    def step_cost(self, source, target):
        return self._edges[(source, target)]


def no_estimate(node):
    return 0.0


def found(events):
    return next((e for e in events if e.kind is EventType.PATH_FOUND), None)


def test_grid_step_cost_is_the_cost_of_entering_the_target_cell():
    grid = Grid.from_text(["S.G"], weights={(0, 1): 7.0})

    assert grid.step_cost((0, 0), (0, 1)) == 7.0
    assert grid.step_cost((0, 2), (0, 1)) == 7.0


def test_grid_step_cost_is_one_for_unweighted_cells():
    grid = Grid.from_text(["S.G"])

    assert grid.step_cost((0, 0), (0, 1)) == 1.0


def test_the_cost_of_entering_a_node_can_depend_on_the_road_taken():
    graph = Graph(
        "A",
        "D",
        {("A", "B"): 1.0, ("A", "C"): 2.0, ("B", "D"): 5.0, ("C", "D"): 1.0},
    )

    result = found(list(best_first(graph, no_estimate)))

    assert result.path == ("A", "C", "D")
    assert result.cost == 3.0


def test_a_cheaper_route_to_a_known_node_is_reported_as_an_update():
    graph = Graph(
        "A",
        "D",
        {("A", "B"): 10.0, ("A", "C"): 1.0, ("C", "B"): 1.0, ("B", "D"): 1.0},
    )

    events = list(best_first(graph, no_estimate))

    assert AlgorithmEvent(EventType.NODE_UPDATED, "B", "C", None, 2.0) in events
    assert found(events).path == ("A", "C", "B", "D")


def test_an_unreachable_goal_ends_without_a_path():
    graph = Graph("A", "Z", {("A", "B"): 1.0})

    events = list(best_first(graph, no_estimate))

    assert found(events) is None
    assert events[-1].kind is EventType.COMPLETED

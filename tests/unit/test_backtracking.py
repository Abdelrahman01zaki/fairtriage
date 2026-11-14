from ai_intelligence_lab.algorithms.csp.backtracking import backtracking
from ai_intelligence_lab.algorithms.csp.events import CspEvent, CspEventType
from ai_intelligence_lab.algorithms.csp.problem import Constraint, CspProblem


def different(name, a, b):
    return Constraint(name, (a, b), lambda x, y: x != y)


def never(x, y):
    return False


def kinds(events):
    return [event.kind for event in events]


def solution(events):
    for event in events:
        if event.kind is CspEventType.SOLUTION_FOUND:
            return event.assignment
    return None


def replay(events):
    """Rebuild the assignment from the assign and unassign events alone."""
    assignment = {}
    for event in events:
        if event.kind is CspEventType.VALUE_ASSIGNED:
            assignment[event.variable] = event.value
        elif event.kind is CspEventType.VALUE_UNASSIGNED:
            assert assignment.pop(event.variable) == event.value
    return assignment


def three_way():
    return CspProblem(
        {name: [1, 2, 3] for name in "abc"},
        (
            different("a_ne_b", "a", "b"),
            different("a_ne_c", "a", "c"),
            different("b_ne_c", "b", "c"),
        ),
    )


def unsolvable():
    return CspProblem({"a": [1], "b": [1]}, (different("a_ne_b", "a", "b"),))


def count(events, kind):
    return sum(event.kind is kind for event in events)


def test_single_variable_without_constraints():
    events = list(backtracking(CspProblem({"x": [1, 2]})))

    assert events == [
        CspEvent(CspEventType.STARTED),
        CspEvent(CspEventType.VARIABLE_SELECTED, variable="x"),
        CspEvent(CspEventType.VALUE_ASSIGNED, variable="x", value=1),
        CspEvent(CspEventType.SOLUTION_FOUND, assignment=(("x", 1),)),
        CspEvent(CspEventType.COMPLETED),
    ]


def test_conflict_names_the_broken_unary_rule():
    not_one = Constraint("not_one", ("x",), lambda value: value != 1)

    events = list(backtracking(CspProblem({"x": [1, 2]}, (not_one,))))

    assert events == [
        CspEvent(CspEventType.STARTED),
        CspEvent(CspEventType.VARIABLE_SELECTED, variable="x"),
        CspEvent(CspEventType.VALUE_ASSIGNED, variable="x", value=1),
        CspEvent(CspEventType.CONFLICT, variable="x", value=1, violated=("not_one",)),
        CspEvent(CspEventType.VALUE_UNASSIGNED, variable="x", value=1),
        CspEvent(CspEventType.VALUE_ASSIGNED, variable="x", value=2),
        CspEvent(CspEventType.SOLUTION_FOUND, assignment=(("x", 2),)),
        CspEvent(CspEventType.COMPLETED),
    ]


def test_backtracks_to_the_previous_variable_when_a_domain_runs_out():
    problem = CspProblem(
        {"a": [1, 2], "b": [1]},
        (different("a_ne_b", "a", "b"),),
    )

    events = list(backtracking(problem))

    assert events == [
        CspEvent(CspEventType.STARTED),
        CspEvent(CspEventType.VARIABLE_SELECTED, variable="a"),
        CspEvent(CspEventType.VALUE_ASSIGNED, variable="a", value=1),
        CspEvent(CspEventType.VARIABLE_SELECTED, variable="b"),
        CspEvent(CspEventType.VALUE_ASSIGNED, variable="b", value=1),
        CspEvent(CspEventType.CONFLICT, variable="b", value=1, violated=("a_ne_b",)),
        CspEvent(CspEventType.VALUE_UNASSIGNED, variable="b", value=1),
        CspEvent(CspEventType.VALUE_UNASSIGNED, variable="a", value=1),
        CspEvent(CspEventType.VALUE_ASSIGNED, variable="a", value=2),
        CspEvent(CspEventType.VARIABLE_SELECTED, variable="b"),
        CspEvent(CspEventType.VALUE_ASSIGNED, variable="b", value=1),
        CspEvent(CspEventType.SOLUTION_FOUND, assignment=(("a", 2), ("b", 1))),
        CspEvent(CspEventType.COMPLETED),
    ]


def test_unsolvable_problem_ends_without_a_solution():
    events = list(backtracking(unsolvable()))

    assert solution(events) is None
    assert kinds(events) == [
        CspEventType.STARTED,
        CspEventType.VARIABLE_SELECTED,
        CspEventType.VALUE_ASSIGNED,
        CspEventType.VARIABLE_SELECTED,
        CspEventType.VALUE_ASSIGNED,
        CspEventType.CONFLICT,
        CspEventType.VALUE_UNASSIGNED,
        CspEventType.VALUE_UNASSIGNED,
        CspEventType.COMPLETED,
    ]


def test_conflict_lists_every_broken_rule_in_declared_order():
    problem = CspProblem(
        {"a": [1], "b": [1]},
        (
            Constraint("first_rule", ("a", "b"), never),
            Constraint("second_rule", ("a", "b"), never),
        ),
    )

    events = list(backtracking(problem))

    conflict = next(e for e in events if e.kind is CspEventType.CONFLICT)
    assert conflict.variable == "b"
    assert conflict.violated == ("first_rule", "second_rule")


def test_first_solution_of_a_three_way_all_different_problem():
    events = list(backtracking(three_way()))

    assert solution(events) == (("a", 1), ("b", 2), ("c", 3))
    conflicts = [e.violated for e in events if e.kind is CspEventType.CONFLICT]
    assert conflicts == [("a_ne_b",), ("a_ne_c",), ("b_ne_c",)]


def test_replaying_the_events_rebuilds_the_solution():
    problem = three_way()
    events = list(backtracking(problem))

    rebuilt = replay(events)

    assert rebuilt == dict(solution(events))
    assert problem.is_solution(rebuilt)


def test_a_solved_run_leaves_every_variable_assigned():
    events = list(backtracking(three_way()))

    assigned = count(events, CspEventType.VALUE_ASSIGNED)
    unassigned = count(events, CspEventType.VALUE_UNASSIGNED)

    assert assigned - unassigned == 3


def test_an_unsolved_run_undoes_every_assignment():
    events = list(backtracking(unsolvable()))

    assigned = count(events, CspEventType.VALUE_ASSIGNED)
    unassigned = count(events, CspEventType.VALUE_UNASSIGNED)

    assert assigned == unassigned == 2
    assert replay(events) == {}


def test_generator_is_lazy():
    generator = backtracking(three_way())

    assert next(generator).kind is CspEventType.STARTED
    assert next(generator).kind is CspEventType.VARIABLE_SELECTED


def test_same_problem_gives_same_events():
    problem = three_way()

    assert list(backtracking(problem)) == list(backtracking(problem))

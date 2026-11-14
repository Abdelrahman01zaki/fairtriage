import pytest

from ai_intelligence_lab.algorithms.csp.problem import Constraint, CspProblem


def different_periods(a, b):
    return a[0] != b[0]


def not_double_booked(a, b):
    return a != b


def small_timetable():
    """Two lectures. A value is (period, room)."""
    return CspProblem(
        domains={
            "L1": [("sat9", "A"), ("sat9", "B")],
            "L2": [("sat9", "A"), ("sun9", "A")],
        },
        constraints=(
            Constraint(
                "same_teacher_different_periods", ("L1", "L2"), different_periods
            ),
            Constraint("room_not_double_booked", ("L1", "L2"), not_double_booked),
        ),
    )


# --- Constraint ---------------------------------------------------------


def test_unary_constraint_is_violated_by_a_forbidden_value():
    rule = Constraint("teacher_free_at_sat9", ("L1",), lambda value: value != "sat9")

    assert rule.is_violated({"L1": "sat9"})
    assert not rule.is_violated({"L1": "sun9"})


def test_binary_constraint_checks_both_values_in_scope_order():
    rule = Constraint("before", ("a", "b"), lambda x, y: x < y)

    assert not rule.is_violated({"a": 1, "b": 2})
    assert rule.is_violated({"a": 2, "b": 1})


def test_constraint_with_unassigned_variable_is_not_violated_yet():
    rule = Constraint("never", ("a", "b"), lambda x, y: False)

    assert not rule.is_violated({})
    assert not rule.is_violated({"a": 1})
    assert rule.is_violated({"a": 1, "b": 2})


def test_constraint_rejects_empty_name():
    with pytest.raises(ValueError):
        Constraint("", ("a",), lambda x: True)


def test_constraint_rejects_scope_of_wrong_size():
    with pytest.raises(ValueError):
        Constraint("none", (), lambda: True)
    with pytest.raises(ValueError):
        Constraint("three", ("a", "b", "c"), lambda x, y, z: True)


def test_constraint_rejects_repeated_variable():
    with pytest.raises(ValueError):
        Constraint("twice", ("a", "a"), lambda x, y: True)


# --- CspProblem ---------------------------------------------------------


def test_variables_keep_declaration_order():
    problem = CspProblem({"b": [1], "a": [1], "c": [1]})

    assert problem.variables == ("b", "a", "c")


def test_domains_are_copied_and_frozen():
    values = [1, 2]
    problem = CspProblem({"x": values})

    values.append(3)  # changing the caller's list must not change the problem

    assert problem.domains["x"] == (1, 2)
    with pytest.raises(TypeError):
        problem.domains["x"] = (9,)


def test_problem_rejects_no_variables():
    with pytest.raises(ValueError):
        CspProblem({})


def test_problem_rejects_empty_domain():
    with pytest.raises(ValueError):
        CspProblem({"x": []})


def test_problem_rejects_repeated_values_in_a_domain():
    with pytest.raises(ValueError):
        CspProblem({"x": [1, 1]})


def test_problem_rejects_duplicate_constraint_names():
    rule = Constraint("same", ("x",), lambda value: True)

    with pytest.raises(ValueError):
        CspProblem({"x": [1]}, (rule, rule))


def test_problem_rejects_constraint_on_unknown_variable():
    rule = Constraint("ghost", ("y",), lambda value: True)

    with pytest.raises(ValueError):
        CspProblem({"x": [1]}, (rule,))


# --- Reporting what an assignment breaks ---------------------------------


def test_violated_names_every_broken_rule_in_declared_order():
    problem = small_timetable()

    clash = {"L1": ("sat9", "A"), "L2": ("sat9", "A")}

    assert problem.violated(clash) == (
        "same_teacher_different_periods",
        "room_not_double_booked",
    )


def test_violated_can_name_just_one_rule():
    problem = small_timetable()

    same_period_other_room = {"L1": ("sat9", "B"), "L2": ("sat9", "A")}

    assert problem.violated(same_period_other_room) == (
        "same_teacher_different_periods",
    )


def test_partial_assignment_can_be_consistent():
    problem = small_timetable()

    assert problem.is_consistent({"L1": ("sat9", "A")})
    assert problem.is_consistent({})


def test_is_solution_accepts_a_complete_consistent_assignment():
    problem = small_timetable()

    assert problem.is_solution({"L1": ("sat9", "A"), "L2": ("sun9", "A")})


def test_is_solution_rejects_incomplete_assignment():
    assert not small_timetable().is_solution({"L1": ("sat9", "A")})


def test_is_solution_rejects_value_outside_the_domain():
    problem = small_timetable()

    assert not problem.is_solution({"L1": ("sat9", "A"), "L2": ("mon9", "A")})


def test_is_solution_rejects_unknown_extra_variable():
    problem = small_timetable()
    assignment = {"L1": ("sat9", "A"), "L2": ("sun9", "A"), "L3": ("sat9", "B")}

    assert not problem.is_solution(assignment)


def test_is_solution_rejects_a_complete_assignment_that_breaks_a_rule():
    problem = small_timetable()

    assert not problem.is_solution({"L1": ("sat9", "A"), "L2": ("sat9", "A")})

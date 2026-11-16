import math

import pytest

from ai_intelligence_lab.allocation.model import (
    Allocation,
    AllocationProblem,
    Demand,
    Placement,
    Resource,
    Unplaced,
)


def simple_problem(**overrides):
    parts = {
        "demands": (Demand("d1", 0), Demand("d2", 1)),
        "resources": (Resource("r1", 1), Resource("r2", 2)),
        "cost": {("d1", "r1"): 3.0, ("d2", "r2"): 4.0},
    }
    parts.update(overrides)
    return AllocationProblem(**parts)


# --- Demand -------------------------------------------------------------


def test_a_demand_has_sensible_defaults():
    demand = Demand("d1", 0)

    assert demand.arrived_at == 0.0
    assert demand.needs == frozenset()


def test_a_demand_freezes_its_needs():
    assert Demand("d1", 0, needs=["a", "b"]).needs == frozenset({"a", "b"})


def test_a_demand_needs_given_as_a_string_are_rejected():
    with pytest.raises(ValueError):
        Demand("d1", 0, needs="burns")


def test_a_demand_needs_an_id():
    with pytest.raises(ValueError):
        Demand("", 0)


def test_a_demand_priority_cannot_be_negative():
    with pytest.raises(ValueError):
        Demand("d1", -1)


@pytest.mark.parametrize("bad", [-1.0, math.nan, math.inf])
def test_a_demand_arrival_must_be_a_finite_time_of_zero_or_more(bad):
    with pytest.raises(ValueError):
        Demand("d1", 0, arrived_at=bad)


# --- Resource -----------------------------------------------------------


@pytest.mark.parametrize("capacity", [0, -1])
def test_a_resource_needs_a_positive_capacity(capacity):
    with pytest.raises(ValueError):
        Resource("r1", capacity)


def test_a_resource_serves_demands_whose_needs_it_offers():
    resource = Resource("r1", 1, offers=["burns", "trauma"])

    assert resource.can_serve(Demand("d1", 0))
    assert resource.can_serve(Demand("d2", 0, needs=["burns"]))
    assert not resource.can_serve(Demand("d3", 0, needs=["burns", "icu"]))


# --- AllocationProblem --------------------------------------------------


def test_a_problem_needs_at_least_one_demand():
    with pytest.raises(ValueError):
        simple_problem(demands=())


def test_a_problem_needs_at_least_one_resource():
    with pytest.raises(ValueError):
        simple_problem(resources=())


def test_demand_ids_must_be_unique():
    with pytest.raises(ValueError):
        simple_problem(demands=(Demand("d1", 0), Demand("d1", 1)))


def test_resource_ids_must_be_unique():
    with pytest.raises(ValueError):
        simple_problem(resources=(Resource("r1", 1), Resource("r1", 2)))


def test_a_cost_for_an_unknown_demand_is_rejected():
    with pytest.raises(ValueError):
        simple_problem(cost={("zzz", "r1"): 1.0})


def test_a_cost_for_an_unknown_resource_is_rejected():
    with pytest.raises(ValueError):
        simple_problem(cost={("d1", "zzz"): 1.0})


@pytest.mark.parametrize("bad", [-1.0, math.nan, math.inf])
def test_a_cost_must_be_finite_and_not_negative(bad):
    with pytest.raises(ValueError):
        simple_problem(cost={("d1", "r1"): bad})


def test_cost_of_gives_none_for_a_pair_that_cannot_be_served():
    problem = simple_problem()

    assert problem.cost_of("d1", "r1") == 3.0
    assert problem.cost_of("d1", "r2") is None


# --- Allocation ---------------------------------------------------------


def test_an_allocation_cannot_mention_a_demand_twice():
    with pytest.raises(ValueError):
        Allocation(
            (Placement("d1", "r1", 3.0),),
            (Unplaced("d1", "no room"),),
        )


def test_an_allocation_reports_its_placements():
    allocation = Allocation(
        (Placement("d1", "r1", 3.0), Placement("d2", "r1", 4.0)),
        (Unplaced("d3", "no room"),),
    )

    assert allocation.placement_of("d2") == Placement("d2", "r1", 4.0)
    assert allocation.placement_of("d3") is None
    assert allocation.load("r1") == 2
    assert allocation.load("r2") == 0
    assert allocation.total_cost == pytest.approx(7.0)

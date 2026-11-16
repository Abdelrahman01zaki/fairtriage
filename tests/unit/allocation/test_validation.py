import pytest

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.model import (
    Allocation,
    AllocationProblem,
    Demand,
    Placement,
    Resource,
    Unplaced,
)
from ai_intelligence_lab.allocation.validation import validate_allocation


def problem():
    return AllocationProblem(
        (Demand("d1", 0), Demand("d2", 1, needs=["burns"]), Demand("d3", 2)),
        (Resource("r1", 1), Resource("r2", 1, offers=["burns"])),
        {
            ("d1", "r1"): 1.0,
            ("d2", "r1"): 1.0,
            ("d2", "r2"): 3.0,
            ("d3", "r1"): 1.0,
        },
    )


def test_a_greedy_allocation_is_accepted():
    validate_allocation(problem(), greedy_allocate(problem()))


def test_a_resource_over_its_capacity_is_rejected():
    allocation = Allocation(
        (
            Placement("d1", "r1", 1.0),
            Placement("d3", "r1", 1.0),
            Placement("d2", "r2", 3.0),
        )
    )

    with pytest.raises(ValueError):
        validate_allocation(problem(), allocation)


def test_a_resource_that_does_not_offer_the_need_is_rejected():
    allocation = Allocation(
        (Placement("d2", "r1", 1.0),),
        (Unplaced("d1", "x"), Unplaced("d3", "x")),
    )

    with pytest.raises(ValueError):
        validate_allocation(problem(), allocation)


def test_a_pair_the_problem_says_cannot_be_served_is_rejected():
    allocation = Allocation(
        (Placement("d1", "r2", 2.0),),
        (Unplaced("d2", "x"), Unplaced("d3", "x")),
    )

    with pytest.raises(ValueError):
        validate_allocation(problem(), allocation)


def test_a_cost_different_from_the_problems_is_rejected():
    allocation = Allocation(
        (Placement("d1", "r1", 9.0),),
        (Unplaced("d2", "x"), Unplaced("d3", "x")),
    )

    with pytest.raises(ValueError):
        validate_allocation(problem(), allocation)


def test_a_demand_that_is_not_answered_is_rejected():
    allocation = Allocation((Placement("d1", "r1", 1.0),), (Unplaced("d2", "x"),))

    with pytest.raises(ValueError):
        validate_allocation(problem(), allocation)


def test_an_unknown_resource_is_rejected():
    allocation = Allocation(
        (Placement("d1", "zzz", 1.0),),
        (Unplaced("d2", "x"), Unplaced("d3", "x")),
    )

    with pytest.raises(ValueError):
        validate_allocation(problem(), allocation)

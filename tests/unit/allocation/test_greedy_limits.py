"""What the greedy baseline cannot do, written down as a test.

Greedy gives each demand, most urgent first, the cheapest place that is free.
It never asks whether that place is the only one a later demand can use. A
smarter allocator is measured against exactly this case.
"""

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.model import (
    Allocation,
    AllocationProblem,
    Demand,
    Placement,
    Resource,
)
from ai_intelligence_lab.allocation.validation import validate_allocation


def burns_conflict() -> AllocationProblem:
    """The plain urgent demand is cheapest at the only burns unit."""
    return AllocationProblem(
        (
            Demand("red", 0),
            Demand("yellow", 1, needs=frozenset({"burns"})),
        ),
        (
            Resource("burns-unit", 1, frozenset({"burns"})),
            Resource("general", 1),
        ),
        {
            ("red", "burns-unit"): 4.0,
            ("red", "general"): 10.0,
            ("yellow", "burns-unit"): 4.0,
        },
    )


def test_a_legal_answer_places_everyone():
    problem = burns_conflict()
    better = Allocation(
        (
            Placement("red", "general", 10.0),
            Placement("yellow", "burns-unit", 4.0),
        )
    )

    validate_allocation(problem, better)

    assert better.unplaced == ()


def test_greedy_takes_the_only_burns_bed_and_leaves_the_burns_case_unplaced():
    problem = burns_conflict()

    result = greedy_allocate(problem)

    validate_allocation(problem, result)
    placed = result.placement_of("red")
    assert placed is not None
    assert placed.resource_id == "burns-unit"
    assert [item.demand_id for item in result.unplaced] == ["yellow"]
    assert result.unplaced[0].reason == "every suitable resource is full"

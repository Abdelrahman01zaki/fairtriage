import random

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.model import (
    AllocationProblem,
    Demand,
    Resource,
)
from ai_intelligence_lab.allocation.validation import validate_allocation


def build(demands, resources, costs):
    return AllocationProblem(tuple(demands), tuple(resources), costs)


def test_the_most_urgent_demand_gets_the_cheapest_resource():
    problem = build(
        [Demand("red", 0, arrived_at=5.0), Demand("yellow", 1, arrived_at=0.0)],
        [Resource("near", 1), Resource("far", 1)],
        {
            ("red", "near"): 1.0,
            ("red", "far"): 5.0,
            ("yellow", "near"): 1.0,
            ("yellow", "far"): 5.0,
        },
    )

    allocation = greedy_allocate(problem)

    assert allocation.placement_of("red").resource_id == "near"
    assert allocation.placement_of("yellow").resource_id == "far"


def test_among_equal_priorities_the_one_waiting_longest_goes_first():
    problem = build(
        [Demand("late", 0, arrived_at=2.0), Demand("early", 0, arrived_at=1.0)],
        [Resource("near", 1), Resource("far", 1)],
        {
            ("late", "near"): 1.0,
            ("late", "far"): 5.0,
            ("early", "near"): 1.0,
            ("early", "far"): 5.0,
        },
    )

    allocation = greedy_allocate(problem)

    assert allocation.placement_of("early").resource_id == "near"
    assert allocation.placement_of("late").resource_id == "far"


def test_equal_costs_are_broken_by_resource_id():
    problem = build(
        [Demand("d1", 0)],
        [Resource("b", 1), Resource("a", 1)],
        {("d1", "b"): 2.0, ("d1", "a"): 2.0},
    )

    assert greedy_allocate(problem).placement_of("d1").resource_id == "a"


def test_capacity_is_respected_and_the_least_urgent_is_left_out():
    problem = build(
        [Demand("d1", 0), Demand("d2", 1), Demand("d3", 2)],
        [Resource("r1", 2)],
        {("d1", "r1"): 1.0, ("d2", "r1"): 1.0, ("d3", "r1"): 1.0},
    )

    allocation = greedy_allocate(problem)

    assert [item.demand_id for item in allocation.placements] == ["d1", "d2"]
    assert [item.demand_id for item in allocation.unplaced] == ["d3"]


def test_a_demand_only_goes_where_its_needs_are_offered():
    problem = build(
        [Demand("d1", 0, needs=["burns"])],
        [Resource("cheap", 1), Resource("burn-unit", 1, offers=["burns"])],
        {("d1", "cheap"): 1.0, ("d1", "burn-unit"): 9.0},
    )

    assert greedy_allocate(problem).placement_of("d1").resource_id == "burn-unit"


def test_the_reason_names_a_missing_capability():
    problem = build(
        [Demand("d1", 0, needs=["burns"])],
        [Resource("r1", 1)],
        {("d1", "r1"): 1.0},
    )

    reason = greedy_allocate(problem).unplaced[0].reason

    assert "burns" in reason


def test_the_reason_says_when_no_suitable_resource_can_be_reached():
    problem = build([Demand("d1", 0)], [Resource("r1", 1)], {})

    reason = greedy_allocate(problem).unplaced[0].reason

    assert reason == "no suitable resource can be reached"


def test_the_reason_says_when_every_suitable_resource_is_full():
    problem = build(
        [Demand("d1", 0), Demand("d2", 1)],
        [Resource("r1", 1)],
        {("d1", "r1"): 1.0, ("d2", "r1"): 1.0},
    )

    reason = greedy_allocate(problem).unplaced[0].reason

    assert reason == "every suitable resource is full"


def test_the_order_the_demands_are_given_in_does_not_change_the_answer():
    demands = [Demand("a", 1), Demand("b", 0), Demand("c", 1, arrived_at=3.0)]
    resources = [Resource("r1", 1), Resource("r2", 1)]
    costs = {
        (demand.id, resource.id): float(index + 1)
        for index, demand in enumerate(demands)
        for resource in resources
    }

    forward = greedy_allocate(build(demands, resources, costs))
    backward = greedy_allocate(build(reversed(demands), resources, costs))

    assert forward == backward


def test_random_problems_always_give_a_legal_allocation():
    for seed in range(30):
        rng = random.Random(seed)
        demands = [
            Demand(
                f"d{i}",
                rng.randint(0, 3),
                arrived_at=rng.uniform(0, 10),
                needs=rng.sample(["a", "b"], rng.randint(0, 2)),
            )
            for i in range(rng.randint(1, 8))
        ]
        resources = [
            Resource(
                f"r{j}",
                rng.randint(1, 3),
                offers=rng.sample(["a", "b"], rng.randint(0, 2)),
            )
            for j in range(rng.randint(1, 4))
        ]
        costs = {
            (demand.id, resource.id): rng.uniform(0, 10)
            for demand in demands
            for resource in resources
            if rng.random() < 0.7
        }
        problem = build(demands, resources, costs)

        allocation = greedy_allocate(problem)

        validate_allocation(problem, allocation)
        assert allocation == greedy_allocate(problem)

import itertools
import random
from collections import Counter

import pytest

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.model import AllocationProblem, Demand, Resource
from ai_intelligence_lab.allocation.optimal import optimal_allocate
from ai_intelligence_lab.allocation.validation import validate_allocation
from ai_intelligence_lab.environments.road_network import Junction, Road, RoadNetwork
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.simulation.engine import simulate
from ai_intelligence_lab.fairtriage.simulation.scenario import Scenario


def burns_conflict() -> AllocationProblem:
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


def test_the_burns_conflict_places_everyone():
    problem = burns_conflict()

    result = optimal_allocate(problem)

    validate_allocation(problem, result)
    assert result.unplaced == ()
    assert result.placement_of("red").resource_id == "general"
    assert result.placement_of("yellow").resource_id == "burns-unit"


def test_the_more_urgent_demand_wins_even_when_it_costs_more():
    problem = AllocationProblem(
        (Demand("red", 0), Demand("green", 2)),
        (Resource("only", 1),),
        {("red", "only"): 100.0, ("green", "only"): 1.0},
    )

    result = optimal_allocate(problem)

    validate_allocation(problem, result)
    assert [item.demand_id for item in result.placements] == ["red"]
    assert [item.demand_id for item in result.unplaced] == ["green"]


def test_among_equal_counts_the_total_cost_is_the_lowest():
    problem = AllocationProblem(
        (Demand("a", 1), Demand("b", 1)),
        (Resource("x", 1), Resource("y", 1)),
        {
            ("a", "x"): 1.0,
            ("a", "y"): 2.0,
            ("b", "x"): 2.0,
            ("b", "y"): 10.0,
        },
    )

    result = optimal_allocate(problem)

    validate_allocation(problem, result)
    assert result.total_cost == pytest.approx(4.0)


def test_the_urgent_demand_is_placed_even_if_two_less_urgent_could_take_its_place():
    problem = AllocationProblem(
        (Demand("red", 0), Demand("green-1", 2), Demand("green-2", 2)),
        (Resource("A", 1), Resource("B", 1)),
        {
            ("red", "A"): 5.0,
            ("red", "B"): 5.0,
            ("green-1", "A"): 1.0,
            ("green-2", "B"): 1.0,
        },
    )

    result = optimal_allocate(problem)

    validate_allocation(problem, result)
    assert result.placement_of("red") is not None
    assert len(result.placements) == 2


def test_each_unplaced_demand_says_why():
    problem = AllocationProblem(
        (
            Demand("picky", 0, needs=frozenset({"burns"})),
            Demand("first", 0),
            Demand("cut-off", 1),
            Demand("late", 2),
        ),
        (Resource("room", 1), Resource("island", 1)),
        {("first", "room"): 3.0, ("late", "room"): 3.0},
    )

    result = optimal_allocate(problem)

    validate_allocation(problem, result)
    assert [item.demand_id for item in result.placements] == ["first"]
    reasons = {item.demand_id: item.reason for item in result.unplaced}
    assert reasons == {
        "picky": "no resource offers what is needed (burns)",
        "cut-off": "no suitable resource can be reached",
        "late": "every suitable resource is full",
    }


def test_the_same_problem_always_gives_the_same_answer():
    problem = burns_conflict()

    assert optimal_allocate(problem) == optimal_allocate(problem)


def random_problem(seed: int) -> AllocationProblem:
    rng = random.Random(seed)
    options = [(), ("x",)]
    demands = tuple(
        Demand(f"d{i}", rng.randint(0, 2), needs=frozenset(rng.choice(options)))
        for i in range(rng.randint(1, 5))
    )
    resources = tuple(
        Resource(f"r{i}", rng.randint(1, 2), frozenset(rng.choice(options)))
        for i in range(rng.randint(1, 3))
    )
    cost = {
        (demand.id, resource.id): float(rng.randint(1, 20))
        for demand in demands
        for resource in resources
        if rng.random() < 0.8
    }
    return AllocationProblem(demands, resources, cost)


def score(problem: AllocationProblem, chosen: dict[str, str]):
    """Lower is better: fewer urgent demands left out first, then less cost."""
    levels = sorted({demand.priority for demand in problem.demands})
    served = tuple(
        -sum(
            1
            for demand in problem.demands
            if demand.priority == level and demand.id in chosen
        )
        for level in levels
    )
    cost = sum(problem.cost_of(demand_id, rid) for demand_id, rid in chosen.items())
    return served, cost


def best_possible(problem: AllocationProblem):
    """Try every way of placing the demands and keep the best score."""
    choices = [
        [
            None,
            *(
                resource.id
                for resource in problem.resources
                if resource.can_serve(demand)
                and problem.cost_of(demand.id, resource.id) is not None
            ),
        ]
        for demand in problem.demands
    ]
    capacity = {resource.id: resource.capacity for resource in problem.resources}
    best = None
    for combo in itertools.product(*choices):
        chosen = {
            demand.id: rid
            for demand, rid in zip(problem.demands, combo, strict=True)
            if rid is not None
        }
        load = Counter(chosen.values())
        if any(load[rid] > capacity[rid] for rid in load):
            continue
        found = score(problem, chosen)
        if best is None or found < best:
            best = found
    return best


def test_the_answer_is_as_good_as_trying_every_possibility():
    for seed in range(300):
        problem = random_problem(seed)

        result = optimal_allocate(problem)

        validate_allocation(problem, result)
        chosen = {item.demand_id: item.resource_id for item in result.placements}
        served, cost = score(problem, chosen)
        best_served, best_cost = best_possible(problem)
        assert served == best_served, f"seed {seed}"
        assert cost == pytest.approx(best_cost), f"seed {seed}"


def test_in_a_simulation_the_optimal_allocator_serves_the_burns_case_greedy_misses():
    network = RoadNetwork(
        (
            Junction("BASE", 0.0, 0.0),
            Junction("SCENE", 2.0, 0.0),
            Junction("BURNS", 6.0, 0.0),
            Junction("GENERAL", 2.0, 10.0),
        ),
        (
            Road("BASE", "SCENE", 2.0),
            Road("SCENE", "BURNS", 4.0),
            Road("SCENE", "GENERAL", 10.0),
        ),
    )
    incident = Incident(
        "I-1",
        "SCENE",
        (
            Casualty("R", TriageCategory.RED, 0.0),
            Casualty("Y", TriageCategory.YELLOW, 0.0, frozenset({"burns"})),
        ),
    )
    scenario = Scenario(
        network,
        incident,
        (
            Hospital("H-burns", "BURNS", 1, frozenset({"burns"})),
            Hospital("H-general", "GENERAL", 1),
        ),
        (Ambulance("A1", "BASE"), Ambulance("A2", "BASE")),
    )

    greedy = simulate(scenario, allocator=greedy_allocate)
    optimal = simulate(scenario, allocator=optimal_allocate)

    assert greedy.unserved == ("Y",)
    assert optimal.unserved == ()
    assert optimal.transport_of("R").hospital_id == "H-general"
    assert optimal.transport_of("Y").hospital_id == "H-burns"

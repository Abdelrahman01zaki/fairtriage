"""One check that any allocator's answer must pass."""

import math

from ai_intelligence_lab.allocation.model import Allocation, AllocationProblem


def validate_allocation(problem: AllocationProblem, allocation: Allocation) -> None:
    """Raise ValueError unless ``allocation`` is a legal answer to ``problem``.

    Every demand must be either placed or left unplaced, exactly once. Every
    placement must use a resource that offers what the demand needs, at the
    cost the problem states, and no resource may hold more than its capacity.
    """
    demands = {demand.id: demand for demand in problem.demands}
    resources = {resource.id: resource for resource in problem.resources}

    answered = {item.demand_id for item in allocation.placements}
    answered |= {item.demand_id for item in allocation.unplaced}
    if answered != set(demands):
        raise ValueError("the allocation must answer every demand exactly once")

    load: dict[str, int] = {}
    for placement in allocation.placements:
        demand = demands[placement.demand_id]
        resource = resources.get(placement.resource_id)
        if resource is None:
            raise ValueError(f"unknown resource {placement.resource_id!r}")
        if not resource.can_serve(demand):
            raise ValueError(
                f"resource {resource.id!r} does not offer what "
                f"demand {demand.id!r} needs"
            )
        cost = problem.cost_of(demand.id, resource.id)
        if cost is None:
            raise ValueError(
                f"demand {demand.id!r} cannot be served at resource {resource.id!r}"
            )
        if not math.isclose(placement.cost, cost, abs_tol=1e-9):
            raise ValueError(
                f"demand {demand.id!r} at {resource.id!r} is placed at cost "
                f"{placement.cost}, but the problem says {cost}"
            )
        load[resource.id] = load.get(resource.id, 0) + 1

    for resource_id, used in load.items():
        if used > resources[resource_id].capacity:
            raise ValueError(f"resource {resource_id!r} is over its capacity")

"""The simple baseline: serve the most urgent demand first, cheapest place first.

Demands are taken by priority, then by how long they have been waiting, then
by id, so the same problem always gives the same answer. Each demand takes the
cheapest resource that can serve it and still has room. This is how a person
under pressure would do it, which is why it is the yardstick that smarter
allocators are measured against.
"""

from ai_intelligence_lab.allocation.model import (
    Allocation,
    AllocationProblem,
    Demand,
    Placement,
    Unplaced,
)


def greedy_allocate(problem: AllocationProblem) -> Allocation:
    free = {resource.id: resource.capacity for resource in problem.resources}
    order = sorted(
        problem.demands,
        key=lambda demand: (demand.priority, demand.arrived_at, demand.id),
    )

    placements: list[Placement] = []
    unplaced: list[Unplaced] = []
    for demand in order:
        best: tuple[float, str] | None = None
        for resource in problem.resources:
            if free[resource.id] == 0 or not resource.can_serve(demand):
                continue
            cost = problem.cost_of(demand.id, resource.id)
            if cost is None:
                continue
            if best is None or (cost, resource.id) < best:
                best = (cost, resource.id)

        if best is None:
            unplaced.append(Unplaced(demand.id, _why_not(problem, demand)))
            continue
        cost, resource_id = best
        free[resource_id] -= 1
        placements.append(Placement(demand.id, resource_id, cost))

    return Allocation(tuple(placements), tuple(unplaced))


def _why_not(problem: AllocationProblem, demand: Demand) -> str:
    capable = [r for r in problem.resources if r.can_serve(demand)]
    if not capable:
        wanted = ", ".join(sorted(demand.needs))
        return f"no resource offers what is needed ({wanted})"
    if all(problem.cost_of(demand.id, r.id) is None for r in capable):
        return "no suitable resource can be reached"
    return "every suitable resource is full"

"""The optimal allocator: the best answer under a stated order of goals.

The goals, in this order:

1. serve as many of the most urgent demands as possible,
2. then as many of the next most urgent, and so on down,
3. then keep the total cost as low as possible.

The greedy baseline decides one demand at a time and never looks back. This
allocator decides all of them together, so it can send an urgent demand to a
farther place to keep the only suitable place free for a demand that has no
other.

It is a min-cost flow, solved exactly with fractions so that no rounding can
change the order of the goals. Each placed demand earns a reward larger than
everything that could be gained below it, so the cheapest flow is also the best
answer by the order above. Ties are broken by the order in which demands and
resources are given, so the same problem always gives the same allocation.
"""

from fractions import Fraction

from ai_intelligence_lab.allocation.greedy import _why_not
from ai_intelligence_lab.allocation.model import (
    Allocation,
    AllocationProblem,
    Placement,
    Unplaced,
)

_Pair = tuple[int, int, float]


def optimal_allocate(problem: AllocationProblem) -> Allocation:
    demands = problem.demands
    resources = problem.resources

    pairs: list[_Pair] = []
    for d, demand in enumerate(demands):
        for r, resource in enumerate(resources):
            cost = problem.cost_of(demand.id, resource.id)
            if cost is not None and resource.can_serve(demand):
                pairs.append((d, r, cost))

    reward = _rewards(problem, pairs)
    source = 0
    first_resource = 1 + len(demands)
    sink = first_resource + len(resources)
    network = _Network(sink + 1)

    for d in range(len(demands)):
        network.add(source, 1 + d, 1, Fraction(0))
    edges: list[tuple[int, int, float, int]] = []
    for d, r, cost in pairs:
        price = Fraction(cost) - reward[demands[d].priority]
        edge = network.add(1 + d, first_resource + r, 1, price)
        edges.append((d, r, cost, edge))
    for r, resource in enumerate(resources):
        network.add(first_resource + r, sink, resource.capacity, Fraction(0))

    network.push_while_cheaper(source, sink)

    placed: dict[int, Placement] = {}
    for d, r, cost, edge in edges:
        if network.is_used(edge):
            placed[d] = Placement(demands[d].id, resources[r].id, cost)

    order = sorted(
        range(len(demands)),
        key=lambda i: (demands[i].priority, demands[i].arrived_at, demands[i].id),
    )
    placements = tuple(placed[i] for i in order if i in placed)
    unplaced = tuple(
        Unplaced(demands[i].id, _why_not(problem, demands[i]))
        for i in order
        if i not in placed
    )
    return Allocation(placements, unplaced)


def _rewards(problem: AllocationProblem, pairs: list[_Pair]) -> dict[int, Fraction]:
    """A reward per priority, each larger than all that the lower ones can give."""
    worst: dict[int, Fraction] = {}
    for d, _, cost in pairs:
        worst[d] = max(worst.get(d, Fraction(0)), Fraction(cost))
    # No answer can cost this much, so cost never outweighs a placement.
    ceiling = Fraction(1) + sum(worst.values(), Fraction(0))

    count: dict[int, int] = {}
    for demand in problem.demands:
        count[demand.priority] = count.get(demand.priority, 0) + 1

    reward: dict[int, Fraction] = {}
    below = Fraction(0)
    for priority in sorted(count, reverse=True):
        reward[priority] = below + ceiling
        below += count[priority] * reward[priority]
    return reward


class _Network:
    """A flow network. Edge ``e`` and its reverse ``e ^ 1`` are stored together."""

    def __init__(self, size: int) -> None:
        self._size = size
        self._out: list[list[int]] = [[] for _ in range(size)]
        self._to: list[int] = []
        self._room: list[int] = []
        self._price: list[Fraction] = []

    def add(self, tail: int, head: int, room: int, price: Fraction) -> int:
        edge = len(self._to)
        self._out[tail].append(edge)
        self._to.append(head)
        self._room.append(room)
        self._price.append(price)
        self._out[head].append(edge + 1)
        self._to.append(tail)
        self._room.append(0)
        self._price.append(-price)
        return edge

    def is_used(self, edge: int) -> bool:
        """True when a one-unit edge carries flow, that is, has no room left."""
        return self._room[edge] == 0

    def push_while_cheaper(self, source: int, sink: int) -> None:
        """Send one unit at a time along the cheapest path while it pays off."""
        while True:
            dist, came = self._cheapest_paths(source)
            reach = dist[sink]
            if reach is None or reach >= 0:
                return
            node = sink
            while node != source:
                edge = came[node]
                self._room[edge] -= 1
                self._room[edge ^ 1] += 1
                node = self._to[edge ^ 1]

    def _cheapest_paths(self, source: int) -> tuple[list[Fraction | None], list[int]]:
        dist: list[Fraction | None] = [None] * self._size
        came = [-1] * self._size
        dist[source] = Fraction(0)
        for _ in range(self._size):
            changed = False
            for node in range(self._size):
                here = dist[node]
                if here is None:
                    continue
                for edge in self._out[node]:
                    if self._room[edge] == 0:
                        continue
                    head = self._to[edge]
                    there = here + self._price[edge]
                    known = dist[head]
                    if known is None or there < known:
                        dist[head] = there
                        came[head] = edge
                        changed = True
            if not changed:
                break
        return dist, came

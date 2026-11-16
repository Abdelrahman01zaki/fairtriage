"""Domain-free model of giving limited resources to demands.

A demand is something that needs a place: a casualty needs a bed, a patient
needs a doctor, a lecture needs a room. A resource is something with a limited
capacity. Nothing here belongs to one field. The application that builds the
problem decides what the words mean.

``cost`` is whatever the application wants to keep small, such as minutes of
travel. A pair that is missing from ``cost`` means that demand cannot be served
by that resource at all.
"""

import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class Demand:
    """Something that needs a place. Priority 0 is the most urgent."""

    id: str
    priority: int
    arrived_at: float = 0.0
    needs: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("a demand needs an id")
        if self.priority < 0:
            raise ValueError(f"demand {self.id!r}: priority cannot be negative")
        if not math.isfinite(self.arrived_at) or self.arrived_at < 0:
            raise ValueError(
                f"demand {self.id!r}: arrived_at must be a finite time of zero or more"
            )
        if isinstance(self.needs, str):
            raise ValueError(f"demand {self.id!r}: needs must be a collection")
        object.__setattr__(self, "needs", frozenset(self.needs))


@dataclass(frozen=True, slots=True)
class Resource:
    """Something that can serve up to ``capacity`` demands."""

    id: str
    capacity: int
    offers: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("a resource needs an id")
        if self.capacity <= 0:
            raise ValueError(f"resource {self.id!r} needs a positive capacity")
        if isinstance(self.offers, str):
            raise ValueError(f"resource {self.id!r}: offers must be a collection")
        object.__setattr__(self, "offers", frozenset(self.offers))

    def can_serve(self, demand: Demand) -> bool:
        """True when this resource offers everything the demand needs."""
        return demand.needs <= self.offers


@dataclass(frozen=True, slots=True)
class AllocationProblem:
    """Demands, resources, and the cost of serving each demand at each one."""

    demands: tuple[Demand, ...]
    resources: tuple[Resource, ...]
    cost: Mapping[tuple[str, str], float]

    def __post_init__(self) -> None:
        demands = tuple(self.demands)
        resources = tuple(self.resources)
        if not demands:
            raise ValueError("a problem needs at least one demand")
        if not resources:
            raise ValueError("a problem needs at least one resource")
        _require_unique("demand id", (demand.id for demand in demands))
        _require_unique("resource id", (resource.id for resource in resources))

        demand_ids = {demand.id for demand in demands}
        resource_ids = {resource.id for resource in resources}
        costs = dict(self.cost)
        for (demand_id, resource_id), value in costs.items():
            if demand_id not in demand_ids:
                raise ValueError(f"cost given for unknown demand {demand_id!r}")
            if resource_id not in resource_ids:
                raise ValueError(f"cost given for unknown resource {resource_id!r}")
            if not math.isfinite(value) or value < 0:
                raise ValueError(
                    f"cost of {demand_id!r} at {resource_id!r} must be "
                    "finite and not negative"
                )

        # Freeze private copies, as Grid does.
        object.__setattr__(self, "demands", demands)
        object.__setattr__(self, "resources", resources)
        object.__setattr__(self, "cost", MappingProxyType(costs))

    def cost_of(self, demand_id: str, resource_id: str) -> float | None:
        """The cost of serving the demand at the resource, or None if it cannot."""
        return self.cost.get((demand_id, resource_id))


@dataclass(frozen=True, slots=True)
class Placement:
    """One demand given a place at one resource, at the problem's cost."""

    demand_id: str
    resource_id: str
    cost: float


@dataclass(frozen=True, slots=True)
class Unplaced:
    """A demand that got no place, with the reason in words."""

    demand_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class Allocation:
    """The answer to a problem: who got a place where, and who got none."""

    placements: tuple[Placement, ...]
    unplaced: tuple[Unplaced, ...] = ()

    def __post_init__(self) -> None:
        placements = tuple(self.placements)
        unplaced = tuple(self.unplaced)
        ids = [item.demand_id for item in placements]
        ids += [item.demand_id for item in unplaced]
        if len(set(ids)) != len(ids):
            raise ValueError("a demand appears more than once in the allocation")
        object.__setattr__(self, "placements", placements)
        object.__setattr__(self, "unplaced", unplaced)

    def placement_of(self, demand_id: str) -> Placement | None:
        for placement in self.placements:
            if placement.demand_id == demand_id:
                return placement
        return None

    def load(self, resource_id: str) -> int:
        """How many demands were placed at this resource."""
        return sum(1 for item in self.placements if item.resource_id == resource_id)

    @property
    def total_cost(self) -> float:
        return sum(item.cost for item in self.placements)


# Anything that turns a problem into an allocation is an allocator.
Allocator = Callable[[AllocationProblem], Allocation]


def _require_unique(what: str, ids: Iterable[str]) -> None:
    seen: set[str] = set()
    for item in ids:
        if item in seen:
            raise ValueError(f"duplicate {what}: {item!r}")
        seen.add(item)

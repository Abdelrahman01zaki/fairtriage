"""A policy is one way to run the simulation: allocator, repositioning, priority.

A runner takes a mapping of name to Policy, so a new baseline or a learned
agent registers as one more entry, without the runner changing.
"""

from dataclasses import dataclass

from ai_intelligence_lab.allocation.model import Allocator
from ai_intelligence_lab.fairtriage.simulation.repositioning import (
    Repositioning,
    return_to_base,
)
from ai_intelligence_lab.fairtriage.transport.priority import PriorityRule, by_urgency


@dataclass(frozen=True, slots=True)
class Policy:
    name: str
    allocator: Allocator
    repositioning: Repositioning = return_to_base
    priority: PriorityRule = by_urgency

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a policy needs a name")

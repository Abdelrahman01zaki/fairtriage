"""How urgent a casualty is, as a rule that can be swapped.

The rule gives each casualty a number, and a smaller number is served first.
The same rule decides who gets a bed (the allocator reads it as the demand's
priority) and who is sent first (the simulation loop sorts by it), so changing
the rule changes both together.

``by_urgency`` is the START triage order. ``fifo`` gives everyone the same
number, so only the time of the report matters: it is the baseline for asking
what triage is worth. Fairness is still measured on each casualty's real
category, whatever rule ran.
"""

from collections.abc import Callable

from ai_intelligence_lab.fairtriage.domain.casualty import Casualty

PriorityRule = Callable[[Casualty], int]


def by_urgency(casualty: Casualty) -> int:
    """START order: 0 is the most urgent."""
    return casualty.category.urgency


def fifo(casualty: Casualty) -> int:
    """Everyone equal, so the first reported is the first served."""
    return 0

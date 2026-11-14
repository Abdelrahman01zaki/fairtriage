"""Event model for constraint satisfaction searches.

CSP searches have their own event type because what happens in them is not a
move through a graph: a variable is chosen, a value is tried, a rule rejects
it, and the choice is undone. Every field has one clear meaning, so a
consumer never has to guess which of them applies.

    STARTED            the run began
    VARIABLE_SELECTED  the search picked ``variable`` to assign next
    VALUE_ASSIGNED     ``variable`` was tried with ``value``
    CONFLICT           that assignment broke the rules named in ``violated``
    VALUE_UNASSIGNED   the assignment of ``variable`` to ``value`` was undone
    SOLUTION_FOUND     every variable has a value; see ``assignment``
    COMPLETED          the run ended

Every VALUE_ASSIGNED is later matched by a VALUE_UNASSIGNED, except for the
assignments that make up the solution. Replaying the events therefore always
rebuilds the current assignment.
"""

from dataclasses import dataclass
from enum import Enum, auto

from ai_intelligence_lab.algorithms.csp.problem import Value, Variable


class CspEventType(Enum):
    STARTED = auto()
    VARIABLE_SELECTED = auto()
    VALUE_ASSIGNED = auto()
    CONFLICT = auto()
    VALUE_UNASSIGNED = auto()
    SOLUTION_FOUND = auto()
    COMPLETED = auto()


@dataclass(frozen=True, slots=True)
class CspEvent:
    """One immutable record of something that happened during a CSP search."""

    kind: CspEventType
    variable: Variable | None = None
    value: Value | None = None
    violated: tuple[str, ...] = ()
    assignment: tuple[tuple[Variable, Value], ...] | None = None

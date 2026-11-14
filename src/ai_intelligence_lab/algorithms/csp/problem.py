"""Generic finite-domain constraint satisfaction model.

A problem is a set of variables, each with a finite domain, plus a list of
named constraints over one or two variables.

Constraints carry a name because an explanation has to say *which* rule
blocked something, in words a person can read. For the same reason the
problem can report exactly which constraints an assignment breaks, instead of
just answering yes or no.
"""

from collections.abc import Callable, Hashable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType

Variable = Hashable
Value = Hashable
Assignment = Mapping[Variable, Value]


@dataclass(frozen=True, slots=True)
class Constraint:
    """A named rule over one or two variables.

    ``allows`` receives the values of the variables in ``scope``, in the same
    order, and returns True when that combination is permitted.
    """

    name: str
    scope: tuple[Variable, ...]
    allows: Callable[..., bool]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a constraint needs a name")
        if len(self.scope) not in (1, 2):
            raise ValueError(
                f"constraint {self.name!r} must cover one or two variables"
            )
        if len(set(self.scope)) != len(self.scope):
            raise ValueError(f"constraint {self.name!r} repeats a variable")

    def is_violated(self, assignment: Assignment) -> bool:
        """True only if every variable in scope is assigned and the rule fails.

        A constraint with an unassigned variable is never violated yet, so a
        partial assignment can be checked while the search is still running.
        """
        if any(variable not in assignment for variable in self.scope):
            return False
        return not self.allows(*(assignment[variable] for variable in self.scope))


@dataclass(frozen=True, slots=True)
class CspProblem:
    """An immutable CSP: variable domains and named constraints."""

    domains: Mapping[Variable, Sequence[Value]]
    constraints: tuple[Constraint, ...] = ()

    def __post_init__(self) -> None:
        # Freeze private copies, as Grid does, so the problem cannot change
        # underneath a running search.
        domains = {var: tuple(values) for var, values in self.domains.items()}
        if not domains:
            raise ValueError("a problem needs at least one variable")
        for variable, values in domains.items():
            if not values:
                raise ValueError(f"variable {variable!r} has an empty domain")
            if len(set(values)) != len(values):
                raise ValueError(f"variable {variable!r} has repeated values")

        constraints = tuple(self.constraints)
        names = [constraint.name for constraint in constraints]
        if len(set(names)) != len(names):
            raise ValueError("constraint names must be unique")
        for constraint in constraints:
            for variable in constraint.scope:
                if variable not in domains:
                    raise ValueError(
                        f"constraint {constraint.name!r} uses "
                        f"unknown variable {variable!r}"
                    )

        object.__setattr__(self, "domains", MappingProxyType(domains))
        object.__setattr__(self, "constraints", constraints)

    @property
    def variables(self) -> tuple[Variable, ...]:
        """Variables in the order they were declared."""
        return tuple(self.domains)

    def violated(self, assignment: Assignment) -> tuple[str, ...]:
        """Names of the constraints this assignment breaks, in declared order."""
        return tuple(
            constraint.name
            for constraint in self.constraints
            if constraint.is_violated(assignment)
        )

    def is_consistent(self, assignment: Assignment) -> bool:
        return not self.violated(assignment)

    def is_solution(self, assignment: Assignment) -> bool:
        """Complete, inside every domain, and breaking no constraint."""
        return (
            set(assignment) == set(self.domains)
            and all(assignment[var] in self.domains[var] for var in self.domains)
            and self.is_consistent(assignment)
        )

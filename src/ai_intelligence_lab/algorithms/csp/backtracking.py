"""Plain backtracking search, written as an event generator.

Variables are taken in the order the problem declares them and values in the
order of each domain, so the same problem always gives the same events.

The search is a loop, not a recursion, so a problem with many variables cannot
hit Python's recursion limit. ``cursor[d]`` is the index of the next value to
try for the variable at depth ``d``, and the length of ``cursor`` is the
current depth.
"""

from collections.abc import Iterator

from ai_intelligence_lab.algorithms.csp.events import CspEvent, CspEventType
from ai_intelligence_lab.algorithms.csp.problem import CspProblem, Value, Variable


def backtracking(problem: CspProblem) -> Iterator[CspEvent]:
    variables = problem.variables
    assignment: dict[Variable, Value] = {}
    cursor = [0]

    yield CspEvent(CspEventType.STARTED)
    yield CspEvent(CspEventType.VARIABLE_SELECTED, variable=variables[0])

    while cursor:
        depth = len(cursor) - 1
        variable = variables[depth]
        domain = problem.domains[variable]

        if cursor[-1] == len(domain):
            # Every value of this variable failed: go back one level.
            cursor.pop()
            if cursor:
                parent = variables[depth - 1]
                yield CspEvent(
                    CspEventType.VALUE_UNASSIGNED,
                    variable=parent,
                    value=assignment.pop(parent),
                )
            continue

        value = domain[cursor[-1]]
        cursor[-1] += 1
        assignment[variable] = value
        yield CspEvent(CspEventType.VALUE_ASSIGNED, variable=variable, value=value)

        broken = problem.violated(assignment)
        if broken:
            yield CspEvent(
                CspEventType.CONFLICT,
                variable=variable,
                value=value,
                violated=broken,
            )
            del assignment[variable]
            yield CspEvent(
                CspEventType.VALUE_UNASSIGNED,
                variable=variable,
                value=value,
            )
        elif depth + 1 == len(variables):
            yield CspEvent(
                CspEventType.SOLUTION_FOUND,
                assignment=tuple(assignment.items()),
            )
            break
        else:
            cursor.append(0)
            yield CspEvent(
                CspEventType.VARIABLE_SELECTED,
                variable=variables[depth + 1],
            )

    yield CspEvent(CspEventType.COMPLETED)

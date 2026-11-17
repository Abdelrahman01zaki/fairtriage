# 2. Require Python 3.11 or newer

Status: accepted

## Context

The project first declared `requires-python = ">=3.10"`. Commit e5eba23 raised
the minimum to 3.11, and its message gives the reason: Python 3.10 reached end
of life in October 2026. That date comes from the commit message and has not
yet been checked against python.org.

The same commit moved `python_version` in the `[tool.mypy]` section from 3.10
to 3.11, so the type checker and the declared minimum agree.

## Decision

Require Python 3.11 or newer. Run CI on Python 3.11 (the minimum) and 3.13.

## Consequences

- The minimum version is tested only by CI. The local environment runs
  Python 3.13 only, so 3.11 has not been run locally.
- Python 3.12 is not in the CI matrix. Behaviour on it is expected to match
  but is not tested.
- Raising the minimum again is a deliberate commit that updates
  `requires-python`, mypy `python_version` and the CI matrix together.

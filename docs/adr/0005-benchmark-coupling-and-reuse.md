# 5. Coupling of the benchmark and what can be reused

Status: accepted

## Context

The `benchmark/` package lives inside `fairtriage/`. Its imports were read:

- `stats.py` imports only the standard library.
- `comparison.py` imports `RunRecord` and `TriageCategory`. The functions
  `category_served_fraction` and `category_horizon_wait` take a category.
- `records.py` imports `CategoryFairness`, `HorizonWaits` and
  `ScenarioSpec`, and `spec_hash` lists the fields of `ScenarioSpec`.
- `storage.py` imports `TriageCategory` and the fairness types.
- `runner.py` imports the fairness report, the generator and the engine.
- `policy.py` imports the repositioning and priority rules.
- `grid.py` and `grid_specialty.py` name `TriageCategory.RED`.

The test `test_architecture.py` covers `allocation` and `simulation`, not
`benchmark`. It looks for imported names that start with
`ai_intelligence_lab.fairtriage`. Reading the code, `from
ai_intelligence_lab import fairtriage` and relative imports would not match
(not tried).

## Decision

Accept this coupling for now. Only `paired_summary` is domain-free, and the
test `test_stats_domain_free.py` (commit e4ba3c5) keeps it so: it fails if
`stats.py` imports anything from this package, absolute or relative.

Do not generalize `RunRecord`, `ScenarioSpec` or `spec_hash` now. Changing
them changes the digests and the pinned file hashes of ADR 0004. If a second
domain is ever added, build a new module beside the existing ones, as
`grid_specialty.py` was built beside `grid.py`, and decide with measurements
whether the duplication is worth it.

## Consequences

- Reusing the harness for another domain needs a new record and spec
  module. The statistics can be reused as they are.
- The gap in `test_architecture.py` is known and not yet closed.
- A "domain-free harness" is a hypothesis, not a claim. Similar frameworks
  for simulation experiments probably exist; that was not searched.

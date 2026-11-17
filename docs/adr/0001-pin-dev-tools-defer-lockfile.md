# 1. Pin development tools, defer the lockfile

Status: accepted

## Context

The project has no runtime dependencies. The development tools are pytest,
ruff and mypy, and results such as test counts, lint findings and type errors
depend on their versions.

Commit 0109576 pinned the three tools with `==` in `pyproject.toml`. Their own
dependencies are not pinned. A fresh install made while checking the Quick
start (November 2026) resolved, for example, `typing_extensions 4.16.0`,
`pathspec 1.1.1` and `librt 0.16.0`, the newest versions available at that
moment. The same command run later may resolve different versions.

## Decision

Pin the three development tools with `==` in `pyproject.toml`. Do not add a
lockfile yet. Revisit this decision when the benchmark harness is built
(roadmap step 4), because published benchmark results must be reproducible
and that needs a full lockfile, for example from `uv`. The tool choice will
be checked against its documentation at that time.

## Consequences

- Test, lint and type-check results for the tools themselves are stable.
- Results can still change if a transitive dependency changes. This is a known
  gap, not a guarantee of reproducibility.
- Upgrading a pinned tool is a deliberate commit that must pass all checks.
- Benchmark results must not be called reproducible until a lockfile exists.

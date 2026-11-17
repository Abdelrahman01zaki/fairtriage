# 6. Pin the Ubuntu runners instead of using ubuntu-latest

Status: accepted

## Context

The CI matrix used `ubuntu-latest`. An excerpt of the GitHub announcement
of 2026-09-17 (the full page was not read) says that label moves from
Ubuntu 24.04 to 26.04 gradually between 2026-10-19 and 2026-11-19. Which
image the runs before #23 got was not recorded: their "Set up job" logs
were not read.

## Decision

The matrix names `ubuntu-24.04` and `ubuntu-26.04` explicitly, each with
Python 3.11 and 3.13, plus `windows-latest` with both. The CI then says
which image passed, instead of following a label that moves. This was
commit e9dc2a3.

## Evidence

CI run #23 on e9dc2a3: all 6 jobs passed (format check, lint, type check
and tests). That is one run. Run time is not recorded here, it varies.

## Not measured

- The "Set up job" image line was not read, so the exact `ubuntu-26.04`
  image version is not recorded.
- The CI does not run the grids or compare sha256 values. Byte-for-byte
  reproduction is measured on one machine with Python 3.13 only (ADR
  0004). Passing tests on 26.04, 3.11 and Windows do not show that the
  output is identical there.
- The retirement date of `ubuntu-24.04` was not searched for.
- `windows-latest` is still a moving label. No announcement was checked.

## Consequences

- 6 jobs per run instead of 4.
- Nothing warns us when `ubuntu-24.04` is retired. Revisit this ADR then,
  and when a newer Ubuntu image appears.
- The follow-up in ADR 0004 (a small sha256 check in CI) is still not
  done. It is now more useful, because 26.04 is in the matrix.

# 4. What "reproducible" means for the benchmark

Status: accepted

## Context

ADR 0001 says benchmark results must not be called reproducible until a
lockfile exists, and asks to revisit that when the benchmark harness is
built. The harness is built, so that condition has come.

A run is a pure function of the scenario spec, the seed and the policy.
Records are written as JSON lines with sorted keys and `\n` line endings,
in the order spec, then seed, then policy, and an existing file is never
overwritten. The `grid` and `grid_specialty` commands print the sha256 of
the file they write.

Measured on one Windows machine with Git Bash and Python 3.13:

- `grid`, 1000 seeds: 72000 records, 104,960,906 bytes, sha256
  `3bbb2179cee1b055f038d699cf791bfd5b6e9b8a0bcd51acd699293807656313`.
  Two runs gave the same file.
- `grid_specialty`, 1000 seeds: 144000 records, 209,808,670 bytes, sha256
  `6b14c08df4f5056ab0b3519cbf7a87ff54c16e2e870312a87fb3b38985b71f5d`.
  Two runs gave the same file.

Run times were 300.1 and 548.1 seconds for `grid`, and 1353.8 and 1260.9
seconds for `grid_specialty`. They vary on the same code for a reason not
found, so they are not performance figures.

Not checked: Python 3.11, another operating system, and the CI. The CI
does not run the grids or compare hashes.

## Decision

Say "two runs gave a byte-identical file on one machine with Python 3.13",
and nothing stronger. Keep ADR 0001 as it stands: no lockfile yet.

The reason is that the project has no runtime dependencies (ADR 0001) and
the benchmark modules import only the standard library and this package
(read in the imports of `benchmark/`; the other packages were not checked).
The pinned development tools do not enter the output. What can change the
output is the Python version, through the standard `random` module. That is
an inference, not a measurement.

## Consequences

- The sha256 values above belong to the code at the time of the runs
  (commits 4a8d87e for `grid` and 4ac1ed1 for `grid_specialty`). A change
  to the generator, the engine or the record format changes them on purpose
  and the new value is recorded in a later ADR.
- Follow-up, not done: a test that compares the sha256 of a small run (for
  example 3 seeds) with a stored value, so the CI checks Python 3.11 and
  3.13 on Ubuntu and Windows. If it fails on 3.11, that is a finding to
  document, not a bug to hide.

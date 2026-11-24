# 3. Scope and limits of the benchmark results

Status: accepted

## Context

The seeded scenario generator and the benchmark harness (roadmap step 1)
now exist. Two grids were run with 1000 seeds each (seeds 0 to 999). Both
use 12 casualties, 3 hospitals, 1 to 4 beds per hospital, 2, 3 or 6
ambulances and a report window of 0, 60 or 240 minutes: 36 cells named
`b{beds}_a{ambulances}_w{window}`.

- `grid`: two policies, greedy allocation with the triage order and greedy
  allocation first come, first served (FIFO).
- `grid_specialty`: one hospital offers a specialty that 25% of the
  casualties need, and four policies: greedy and optimal allocation, each
  with the triage order and with FIFO.

The metric is the share of RED casualties served. A comparison is the
difference between two policies on the same seed, summarized with a
percentile bootstrap interval. At least 100 pairs are required: the module
documents that in a simulation of mostly-zero differences 30 pairs covered
the true mean 91% of the time and 100 pairs between 94.7% and 96%.

## Decision

Report these results only as maps of where an effect appears, and only
together with the following limits.

1. The sizes are illustrative. They are not drawn from real incidents.
2. The generator draws a casualty's category independently of its report
   time, so FIFO behaves like a random order with respect to category.
3. There is no time-dependent harm model. Without a specialty need, the
   total waiting time over all casualties, with the clock stopped at the
   horizon (1500 minutes), was identical under the triage order and under
   FIFO (difference 0.0, for greedy and for optimal). Triage moved waiting
   between categories and did not reduce it. A test guards this. With a
   specialty need it no longer holds (an earlier measurement, not repeated
   in the 1000-seed grids). No claim of benefit is made until a harm model
   exists.
4. The share of RED served is nearly determined for any policy that serves
   RED first. The value of a result is where the difference appears (few
   beds, early reports), not its size.
5. The cells are maps, not 36 or 108 separate tests, and no correction for
   multiple comparisons is applied. An interval that touches zero is not
   reported as an effect.
6. Waits are measured with the clock stopped at the horizon, and
   `waits_to_horizon` raises ValueError for a casualty reported after it.
   Where casualties stay unserved, differences in waiting grow with the
   horizon (a cut effect), so the share served is used there.
7. Each cell has 965 to 968 pairs, not 1000. A scenario without a RED
   casualty gives no value for this metric; the expected share of such
   scenarios with 12 casualties is 0.75^12, about 3.2% (computed by hand,
   not checked in the code).

Results recorded (measured, 1000 seeds):

- `grid`, triage minus FIFO under greedy: largest in `b1_a2_w0` (0.637),
  and exactly zero in all 9 cells with 4 beds per hospital.
- `grid_specialty`, same comparison: `b1_a2_w0` is 0.577 (interval 0.557 to
  0.597), and `b4_a2_w0` is 0.084 (0.072 to 0.095), no longer zero. The
  comparison with `grid` is descriptive: the main generator stream is the
  same, but it is not a test between the two grids. Why the specialty
  lowers the difference in scarce cells has not been tested.
- `grid_specialty`, optimal minus greedy under the triage order: the
  largest mean is 0.027 (0.021 to 0.033) in `b1_a2_w0`, and in no cell was
  optimal ahead in more than 9.7% of the seeds. The share of seeds where
  optimal was behind is not zero in 2 of the 36 cells (`b3_a2_w240` and
  `b3_a3_w240`, 0.001, about one seed). Between `optimal` and
  `optimal_fifo` it is not zero in 3 of 36 cells (`b4_a2_w60`,
  `b4_a2_w240`, `b4_a6_w60`, 0.001 to 0.002). The cause has not been
  investigated. `optimal.py` ranks demands by priority first and cost
  second, but the simulation calls the allocator once for each casualty it
  sends and uses only the first placement of each answer (`engine.py`),
  so the best answer of each call is not the best run. Whether this
  explains these cells was not checked.

## Consequences

- No sentence in the README, a paper or a presentation may say that triage
  helps, only that it changes who waits and when.
- A figure from a probe outside the repository (such as "optimal is better
  in 38 of 100 seeds") must not be quoted until it is recomputed from the
  repository with a named metric.
- Adding a harm model, a generator that links category to report time, or a
  new metric changes what these limits say and needs a new ADR.

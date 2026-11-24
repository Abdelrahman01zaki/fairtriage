# FairTriage

A simulation and evaluation lab for patient-distribution policies in
mass-casualty incidents (MCI): START triage, ambulance dispatch, hospital
allocation and fairness measurement. The goal is to compare different policies
on the same scenario, with results that can be reproduced and inspected,
instead of a black box.

> **Medical disclaimer.** FairTriage is a simulation, research and training
> tool. It is not a medical device and does not replace the judgment of
> paramedics or clinicians. Its output must not be used for real triage or
> dispatch decisions.

> **Status: early research prototype.** The scenarios shipped so far were
> designed by the author to make differences visible. They are illustrations,
> not evidence about how the policies behave in general. See
> [Known limitations](#known-limitations).

## The problem

After a mass-casualty incident there are more injured people than ambulances
and hospital beds. Someone has to decide who is taken first and to which
hospital. FairTriage turns that decision into a policy that can be run on a
simulated incident and measured: who waited, who was never transported, and
how evenly the waiting was shared among casualties of the same START
category. It is a lab for comparing policies, not a tool for making the
decision.

## AI techniques in this project

| Technique | Where (under `src/ai_intelligence_lab/`) |
|-----------|------------------------------------------|
| Search: BFS, DFS, UCS, greedy best-first, A* | `algorithms/search/` |
| Constraint satisfaction: backtracking with named constraints | `algorithms/csp/`, `environments/timetable.py` |
| Route finding for ambulances on a road network | `fairtriage/dispatch/routing.py` |
| Greedy allocation, and exact optimization (min-cost flow in exact fractions, checked against brute force) | `allocation/` |
| Discrete-event simulation | `simulation/event_queue.py`, `fairtriage/simulation/` |
| Evaluation: fairness metrics, paired comparison with a bootstrap interval | `fairtriage/fairness/`, `fairtriage/benchmark/stats.py` |

There is no machine learning and no neural network in the project.

## Background

START (Simple Triage and Rapid Treatment) sorts casualties into RED, YELLOW,
GREEN and BLACK categories. Mills, Argon and Ziya (2013) [1] point out that
START relies on a fixed priority ordering between categories and does not
explicitly consider resource limitations or how survival probabilities change
over time, and they propose a resource-based policy that outperformed START in
their simulation study.

FairTriage does not claim to improve on that work. It is a lab in which the
pieces (triage, routing, allocation, repositioning, fairness) are separate,
tested modules built on classical algorithms, so that policies can be swapped
and compared on the same scenario. Fairness is measured **within** each START
category, because differences between categories are medically intended.

## What is implemented

- Domain model: casualties, incidents, hospitals, ambulances, START categories.
- START classification.
- Dispatch and routing: A* over a road network, nearest available ambulance.
- Hospital allocation: a greedy allocator and an optimal one (min-cost flow
  with a lexicographic objective, checked against brute force in the tests).
- Event-driven simulation with three ambulance repositioning policies:
  `return_to_base`, `stay_at_hospital` and `adaptive`.
- Fairness report per category: wait times, Gini coefficient, time until the
  hospital, and the number of casualties that were never transported.
- Seeded scenario generator: a `ScenarioSpec` and a seed give one
  scenario, with an optional specialty need (one hospital offers a
  specialty that a share of the casualties need).
- A swappable priority rule: START urgency or first come, first served
  (FIFO). The same rule orders dispatch and is the priority the
  allocator sees.
- Benchmark: policies run on many seeds, one flat record per run saved
  as JSON lines, paired differences with bootstrap intervals, and two
  grids run from the command line (see Benchmark).
- Architecture decision records in `docs/adr/`.

The repository grew out of an educational lab for search and CSP algorithms
(BFS, DFS, UCS, greedy, A*, backtracking). Those modules are still in
`src/ai_intelligence_lab/algorithms/`. The generic `allocation` and
`simulation` packages must not import the `fairtriage` package; a test
enforces this.

## Quick start

Requires Python 3.11 or newer.

```bash
git clone https://github.com/Abdelrahman01zaki/fairtriage.git && cd fairtriage
python -m venv .venv && source .venv/bin/activate && python -m pip install -e ".[dev]"
python examples/compare_allocators.py
```

On Windows with Git Bash, activate with `source .venv/Scripts/activate`.

Checks run by CI on Python 3.11 and 3.13 (Ubuntu 24.04, Ubuntu 26.04
and Windows):

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src
python -m pytest -q
```

## Results so far

Both results come from one scenario each, designed by the author. Run
`python examples/compare_repositioning.py` and
`python examples/compare_allocators.py` to reproduce them.

### Ambulance repositioning

Mean minutes a casualty waited for an ambulance, by START category. All 8
casualties were transported under every policy.

| Policy             | Run ends (min) | RED  | YELLOW | GREEN | BLACK |
|--------------------|---------------:|-----:|-------:|------:|------:|
| `return_to_base`   |            128 | 10.0 |   45.0 |  81.0 |  99.0 |
| `stay_at_hospital` |             50 | 10.0 |   18.3 |  31.0 |  39.0 |
| `adaptive`         |             68 | 10.0 |   18.3 |  31.0 |  39.0 |

In this scenario GREEN casualties waited 81 minutes on average (worst 96)
under `return_to_base` and 31 minutes (worst 36) under `stay_at_hospital`.
`adaptive` matched `stay_at_hospital` on waiting times and its run ended later
(minute 68 versus 50), so this scenario shows no advantage for it. A scenario
with several incidents is needed to test what it is designed for.

### Hospital allocation

Six casualties, same incident, two ways of choosing hospitals.

| Allocator | Transported | Never transported | RED reach the hospital at |
|-----------|------------:|-------------------|---------------------------|
| greedy    |      4 of 6 | Y1, Y2            | minute 6                  |
| optimal   |      5 of 6 | G2                | minute 12                 |

The optimal allocator transported one more casualty, both YELLOW casualties
instead of one GREEN, but it delayed the arrival of the RED casualties at the
hospital from minute 6 to minute 12. The optimal allocator maximizes, in
order: the number of the most urgent casualties served, then the next
category, and so on, then it minimizes total minutes. This ordering is a
policy choice, not a medical fact, and whether the 6-minute delay is
acceptable needs expert judgment.

## Known limitations

- The waiting time measures the wait until the ambulance reaches the casualty,
  not until the hospital. Time until the hospital is reported separately.
- There is no loading or unloading time, patients never leave hospital beds,
  and an ambulance heading back to base is not redirected on the way.
- START classification ignores a casualty's `needs`. The needs are passed
  to the allocation problem (`build_transport_problem`).
- The optimal allocator does not favor the casualty who waited longer inside
  the same category.
- The optimal allocator is optimal for each call, one problem at a time.
  The simulation calls it once for every casualty it sends, so a whole
  run is not guaranteed to be optimal.
- The shipped scenarios are hand-designed. A Gini coefficient over two or
  three values is statistically weak.
- "Never transported" means the casualty was not taken to a hospital in the
  simulation. It does not mean the casualty was left without care.
- `mypy --strict` covers `src` only, not tests or examples.
- No real incident data, no review by medical experts and no peer review.

## Benchmark

A grid of 36 scenario cells (1 to 4 beds per hospital, 2, 3 or 6
ambulances, report window 0, 60 or 240 minutes; 12 casualties and 3
hospitals) is run on 1000 seeds under each policy:

```bash
python -m ai_intelligence_lab.fairtriage.benchmark.grid run --out runs/g.jsonl
python -m ai_intelligence_lab.fairtriage.benchmark.grid summarize runs/g.jsonl
```

`grid` compares the triage order with first come, first served (FIFO)
under the greedy allocator. `grid_specialty` adds a specialty hospital
that a quarter of the casualties need, and compares greedy and optimal
allocation under both orders. The measure is the share of RED casualties
served. Each comparison is the difference between two policies on the
same seed, with a bootstrap interval, and needs at least 100 pairs.

What the results say, measured on this generator only (illustrative
sizes, not real incidents):

- Triage changes who is served when beds are scarce and reports arrive
  close together: the largest difference is 0.637 in `b1_a2_w0`
  without a specialty. With 4 beds per hospital and no specialty it was
  exactly 0 in all 9 cells.
- Without a specialty the total waiting over all casualties was the same
  under triage and FIFO. Triage moves waiting between categories and
  does not reduce it. Without a harm model no benefit is claimed.
- With a specialty hospital the difference is smaller in scarce cells
  (0.577 in `b1_a2_w0`) and appears at 4 beds (0.084 in `b4_a2_w0`).
- Optimal against greedy under triage: at most 0.027 on average
  (`b1_a2_w0`), and in no cell was optimal ahead in more than 9.7% of
  the seeds. In a few cells it was behind in one or two seeds; the
  cause was not investigated.

Each cell is a map of where an effect appears, not a separate test. The
limits and the sha256 of both outputs are in `docs/adr/0003` and
`docs/adr/0004`.

## Roadmap

1. Seeded scenario generator and benchmark harness: done (see Benchmark).
   Still open: a time-dependent harm model, and a generator that links a
   casualty's category to its report time.
2. Configurable multi-objective trade-offs and comparison with published
   policies.
3. Dynamic replanning (road closures) and multi-incident coordination.
4. Command-line tool, then renaming the package from `ai_intelligence_lab`
   to `fairtriage`, then an API and a dashboard.

## License

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE).

Copyright 2026 Abdelrahman Zaki AboZena

## References

[1] Mills, A. F., Argon, N. T., and Ziya, S. (2013). Resource-Based Patient
Prioritization in Mass-Casualty Incidents. Manufacturing & Service Operations
Management, 15(3), 361-377. https://doi.org/10.1287/msom.1120.0426

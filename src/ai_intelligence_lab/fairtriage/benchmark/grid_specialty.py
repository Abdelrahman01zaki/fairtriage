"""The specialty grid: every cell run under four policies, saved and summarized.

Same cells as ``grid`` (beds per hospital, ambulances, report window), but one
hospital offers a specialty that a quarter of the casualties need. Without a
specialty need greedy and optimal give identical results, so this is the grid
where optimal can differ. Each cell runs under triage and first-come-first-served,
with a greedy and an optimal allocator.

    python -m ai_intelligence_lab.fairtriage.benchmark.grid_specialty \
        run --out runs/s.jsonl
    python -m ai_intelligence_lab.fairtriage.benchmark.grid_specialty \
        summarize runs/s.jsonl

The sizes are illustrative, not drawn from real incidents. Each comparison is a
map of where an effect shows up, not a separate test.
"""

import argparse
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.optimal import optimal_allocate
from ai_intelligence_lab.fairtriage.benchmark.comparison import (
    category_served_fraction,
    paired_differences,
)
from ai_intelligence_lab.fairtriage.benchmark.grid import (
    AMBULANCES,
    BEDS,
    CASUALTIES,
    HOSPITALS,
    WINDOWS,
    cell_name,
    file_digest,
)
from ai_intelligence_lab.fairtriage.benchmark.policy import Policy
from ai_intelligence_lab.fairtriage.benchmark.records import RunRecord
from ai_intelligence_lab.fairtriage.benchmark.runner import (
    Experiment,
    run_experiment,
)
from ai_intelligence_lab.fairtriage.benchmark.stats import (
    PairedSummary,
    paired_summary,
)
from ai_intelligence_lab.fairtriage.benchmark.storage import (
    read_records,
    write_records,
)
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.scenarios.generator import ScenarioSpec
from ai_intelligence_lab.fairtriage.transport.priority import fifo

SPECIAL_HOSPITALS = 1
SPECIAL_NEED_SHARE = 0.25

GREEDY = "greedy"
GREEDY_FIFO = "greedy_fifo"
OPTIMAL = "optimal"
OPTIMAL_FIFO = "optimal_fifo"

# (first, second): each comparison reports first minus second.
COMPARISONS = (
    (GREEDY, GREEDY_FIFO),
    (OPTIMAL, OPTIMAL_FIFO),
    (OPTIMAL, GREEDY),
)


def grid_specs() -> dict[str, ScenarioSpec]:
    """Every cell of the grid, named, in a fixed order."""
    return {
        cell_name(beds, ambulances, window): ScenarioSpec(
            casualties=CASUALTIES,
            hospitals=HOSPITALS,
            beds_per_hospital=beds,
            ambulances=ambulances,
            report_window=window,
            special_hospitals=SPECIAL_HOSPITALS,
            special_need_share=SPECIAL_NEED_SHARE,
        )
        for beds in BEDS
        for ambulances in AMBULANCES
        for window in WINDOWS
    }


def grid_policies() -> dict[str, Policy]:
    """The four policies, in the order their records are written."""
    return {
        GREEDY: Policy(GREEDY, greedy_allocate),
        GREEDY_FIFO: Policy(GREEDY_FIFO, greedy_allocate, priority=fifo),
        OPTIMAL: Policy(OPTIMAL, optimal_allocate),
        OPTIMAL_FIFO: Policy(OPTIMAL_FIFO, optimal_allocate, priority=fifo),
    }


def run_grid(seeds: Iterable[int]) -> tuple[RunRecord, ...]:
    """Run every cell under all four policies on every seed."""
    return run_experiment(Experiment(grid_specs(), tuple(seeds), grid_policies()))


@dataclass(frozen=True, slots=True)
class ComparisonSummary:
    cell: str
    first: str
    second: str
    summary: PairedSummary


def summarize(
    records: Iterable[RunRecord], *, min_pairs: int = 100
) -> tuple[ComparisonSummary, ...]:
    """Per comparison and cell: first minus second in the share of red served."""
    kept = tuple(records)
    metric = category_served_fraction(TriageCategory.RED)
    rows: list[ComparisonSummary] = []
    for first, second in COMPARISONS:
        for name in grid_specs():
            diffs = paired_differences(kept, name, first, second, metric)
            summary = paired_summary(diffs, min_pairs=min_pairs)
            rows.append(ComparisonSummary(name, first, second, summary))
    return tuple(rows)


def format_table(rows: Iterable[ComparisonSummary]) -> str:
    lines = ["comparison | cell | n mean low high share_pos share_neg"]
    for row in rows:
        s = row.summary
        lines.append(
            f"{row.first}-{row.second} | {row.cell} | {s.n} {s.mean:.3f} "
            f"{s.low:.3f} {s.high:.3f} {s.share_positive:.3f} "
            f"{s.share_negative:.3f}"
        )
    return "\n".join(lines)


def _run(out: Path, seeds: int) -> int:
    if seeds < 1:
        print("--seeds must be at least 1", file=sys.stderr)
        return 2
    if out.exists():
        print(f"{out} already exists; choose a new --out", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    records = run_grid(range(seeds))
    try:
        written = write_records(out, records)
    except FileExistsError:
        print(f"{out} already exists; choose a new --out", file=sys.stderr)
        return 1
    seconds = time.perf_counter() - start
    print(f"records: {written} seconds: {seconds:.1f}")
    print(f"sha256: {file_digest(out)}")
    return 0


def _summarize(path: Path, min_pairs: int) -> int:
    print(format_table(summarize(read_records(path), min_pairs=min_pairs)))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m ai_intelligence_lab.fairtriage.benchmark.grid_specialty",
        description="Run the specialty grid, or summarize a saved run.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run every cell and save the records")
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--seeds", type=int, default=1000)
    read = commands.add_parser("summarize", help="summarize a saved run")
    read.add_argument("path", type=Path)
    read.add_argument("--min-pairs", type=int, default=100)
    args = parser.parse_args(argv)
    if args.command == "run":
        return _run(args.out, args.seeds)
    return _summarize(args.path, args.min_pairs)


if __name__ == "__main__":
    sys.exit(main())

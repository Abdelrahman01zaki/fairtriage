"""The benchmark grid: every cell run under two policies, saved and summarized.

A cell is one ScenarioSpec named by its beds per hospital, ambulances and
report window, for example ``b2_a3_w60``. Every cell is run under triage and
under first-come-first-served on the same seeds, and the difference in the
share of red casualties served is summarized per cell.

Run it, then read the saved file back::

    python -m ai_intelligence_lab.fairtriage.benchmark.grid run --out runs/g.jsonl
    python -m ai_intelligence_lab.fairtriage.benchmark.grid summarize runs/g.jsonl

The sizes are illustrative, not drawn from real incidents. Without a specialty
need greedy and optimal give identical results, so only greedy is run here.
"""

import argparse
import hashlib
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.fairtriage.benchmark.comparison import (
    category_served_fraction,
    paired_differences,
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

CASUALTIES = 12
HOSPITALS = 3
BEDS = (1, 2, 3, 4)
AMBULANCES = (2, 3, 6)
WINDOWS = (0.0, 60.0, 240.0)

TRIAGE = "greedy"
FIRST_COME = "greedy_fifo"


def cell_name(beds: int, ambulances: int, window: float) -> str:
    return f"b{beds}_a{ambulances}_w{int(window)}"


def grid_specs() -> dict[str, ScenarioSpec]:
    """Every cell of the grid, named, in a fixed order."""
    return {
        cell_name(beds, ambulances, window): ScenarioSpec(
            casualties=CASUALTIES,
            hospitals=HOSPITALS,
            beds_per_hospital=beds,
            ambulances=ambulances,
            report_window=window,
        )
        for beds in BEDS
        for ambulances in AMBULANCES
        for window in WINDOWS
    }


def grid_policies() -> dict[str, Policy]:
    return {
        TRIAGE: Policy(TRIAGE, greedy_allocate),
        FIRST_COME: Policy(FIRST_COME, greedy_allocate, priority=fifo),
    }


def run_grid(seeds: Iterable[int]) -> tuple[RunRecord, ...]:
    """Run every cell under both policies on every seed."""
    return run_experiment(Experiment(grid_specs(), tuple(seeds), grid_policies()))


@dataclass(frozen=True, slots=True)
class CellSummary:
    cell: str
    summary: PairedSummary


def summarize(
    records: Iterable[RunRecord], *, min_pairs: int = 100
) -> tuple[CellSummary, ...]:
    """Per cell: triage minus first-come in the share of red casualties served."""
    kept = tuple(records)
    metric = category_served_fraction(TriageCategory.RED)
    rows: list[CellSummary] = []
    for name in grid_specs():
        diffs = paired_differences(kept, name, TRIAGE, FIRST_COME, metric)
        rows.append(CellSummary(name, paired_summary(diffs, min_pairs=min_pairs)))
    return tuple(rows)


def format_table(rows: Iterable[CellSummary]) -> str:
    lines = ["cell | n mean low high share_pos share_neg"]
    for row in rows:
        s = row.summary
        lines.append(
            f"{row.cell} | {s.n} {s.mean:.3f} {s.low:.3f} {s.high:.3f} "
            f"{s.share_positive:.3f} {s.share_negative:.3f}"
        )
    return "\n".join(lines)


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        prog="python -m ai_intelligence_lab.fairtriage.benchmark.grid",
        description="Run the triage grid, or summarize a saved run.",
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

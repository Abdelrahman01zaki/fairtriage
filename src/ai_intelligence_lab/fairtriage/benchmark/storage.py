"""Save RunRecords as JSON lines and read them back.

One record per line, so a long experiment can be inspected, appended to or
streamed. A line written before a field existed reads back with that field's
default, which is why every later field of RunRecord must have one.
"""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ai_intelligence_lab.fairtriage.benchmark.records import RunRecord, to_json_dict
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.fairness.metrics import (
    CategoryFairness,
    HorizonWaits,
)


def from_json_dict(row: dict[str, Any]) -> RunRecord:
    """The inverse of ``to_json_dict``; missing optional fields take defaults."""
    categories = tuple(
        CategoryFairness(
            TriageCategory[item["category"]],
            item["transported"],
            item["unserved"],
            item["mean_wait"],
            item["median_wait"],
            item["worst_wait"],
            item["gini"],
            item.get("mean_to_hospital"),
            item.get("worst_to_hospital"),
        )
        for item in row["categories"]
    )
    horizon_waits = tuple(
        HorizonWaits(
            TriageCategory[item["category"]],
            item["count"],
            item["mean_wait"],
            item["gini"],
        )
        for item in row.get("horizon_waits", [])
    )
    return RunRecord(
        row["schema_version"],
        row["spec_name"],
        row["spec_hash"],
        row["seed"],
        row["policy_name"],
        row["served"],
        row["unserved_total"],
        row["end_time"],
        categories,
        horizon_waits,
        row.get("horizon", 0.0),
    )


def write_records(path: Path, records: Iterable[RunRecord]) -> int:
    """Write one JSON line per record to a new file; return how many were written.

    An existing file is never overwritten: it raises FileExistsError.
    """
    count = 0
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(to_json_dict(record), sort_keys=True) + "\n")
            count += 1
    return count


def read_records(path: Path) -> tuple[RunRecord, ...]:
    """Every record in ``path``. A bad line raises ValueError naming its number."""
    records: list[RunRecord] = []
    with path.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(from_json_dict(json.loads(line)))
            except (KeyError, ValueError, TypeError) as error:
                raise ValueError(f"{path}: line {number}: {error!r}") from error
    return tuple(records)

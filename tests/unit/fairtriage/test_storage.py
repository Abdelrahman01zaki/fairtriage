import json

import pytest

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.fairtriage.benchmark.policy import Policy
from ai_intelligence_lab.fairtriage.benchmark.runner import run_once
from ai_intelligence_lab.fairtriage.benchmark.storage import (
    read_records,
    write_records,
)
from ai_intelligence_lab.fairtriage.scenarios.generator import ScenarioSpec
from ai_intelligence_lab.fairtriage.transport.priority import fifo

# 6 casualties for 2 beds, so some categories end with nobody transported.
_SCARCE = ScenarioSpec(
    casualties=6,
    hospitals=2,
    beds_per_hospital=1,
    ambulances=2,
    junctions=4,
    extra_roads=0,
)
_POLICIES = (
    Policy("greedy", greedy_allocate),
    Policy("greedy_fifo", greedy_allocate, priority=fifo),
)


def _records():
    return [
        run_once("scarce", _SCARCE, seed, policy)
        for seed in range(5)
        for policy in _POLICIES
    ]


def test_records_read_back_equal_to_what_was_written(tmp_path):
    path = tmp_path / "runs.jsonl"
    records = _records()
    assert any(item.mean_wait is None for r in records for item in r.categories)

    assert write_records(path, records) == len(records)

    assert list(read_records(path)) == records


def test_a_line_from_before_the_horizon_fields_reads_with_defaults(tmp_path):
    record = run_once("scarce", _SCARCE, seed=1, policy=_POLICIES[0])
    path = tmp_path / "old.jsonl"
    write_records(path, [record])
    row = json.loads(path.read_text(encoding="utf-8"))
    del row["horizon_waits"], row["horizon"]
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    (old,) = read_records(path)

    assert old.horizon_waits == ()
    assert old.horizon == 0.0
    assert old.served == record.served


def test_an_existing_file_is_never_overwritten(tmp_path):
    path = tmp_path / "runs.jsonl"
    path.write_text("keep\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_records(path, _records())

    assert path.read_text(encoding="utf-8") == "keep\n"


def test_a_bad_line_is_reported_with_its_number(tmp_path):
    path = tmp_path / "runs.jsonl"
    write_records(path, _records()[:2])
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{not json}\n")

    with pytest.raises(ValueError, match="line 3"):
        read_records(path)


def test_blank_lines_are_skipped(tmp_path):
    path = tmp_path / "runs.jsonl"
    records = _records()[:2]
    write_records(path, records)
    text = path.read_text(encoding="utf-8")
    path.write_text(f"\n{text}\n\n", encoding="utf-8")

    assert list(read_records(path)) == records

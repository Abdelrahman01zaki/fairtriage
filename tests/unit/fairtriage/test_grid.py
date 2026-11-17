import pytest

from ai_intelligence_lab.fairtriage.benchmark.grid import (
    FIRST_COME,
    TRIAGE,
    cell_name,
    file_digest,
    grid_specs,
    main,
    run_grid,
    summarize,
)


@pytest.fixture(scope="module")
def records():
    return run_grid(range(3))


def test_the_grid_has_36_distinct_cells():
    assert len(grid_specs()) == 36


def test_every_cell_name_describes_its_spec():
    for name, spec in grid_specs().items():
        expected = cell_name(
            spec.beds_per_hospital, spec.ambulances, spec.report_window
        )
        assert name == expected


def test_every_cell_runs_both_policies_on_every_seed(records):
    seen = {(r.spec_name, r.seed, r.policy_name) for r in records}

    assert len(records) == 36 * 2 * 3
    assert len(seen) == len(records)
    assert {r.policy_name for r in records} == {TRIAGE, FIRST_COME}


def test_summarize_gives_one_row_per_cell(records):
    rows = summarize(records, min_pairs=1)

    assert [row.cell for row in rows] == list(grid_specs())


def test_run_then_summarize_through_the_command_line(tmp_path, capsys):
    out = tmp_path / "runs" / "grid.jsonl"

    assert main(["run", "--out", str(out), "--seeds", "3"]) == 0
    assert len(out.read_text(encoding="utf-8").splitlines()) == 36 * 2 * 3
    assert main(["summarize", str(out), "--min-pairs", "1"]) == 0

    assert "b1_a2_w0" in capsys.readouterr().out


def test_the_same_run_twice_gives_byte_identical_files(tmp_path):
    first, second = tmp_path / "a.jsonl", tmp_path / "b.jsonl"

    main(["run", "--out", str(first), "--seeds", "3"])
    main(["run", "--out", str(second), "--seeds", "3"])

    assert file_digest(first) == file_digest(second)


def test_an_existing_output_file_is_not_overwritten(tmp_path):
    out = tmp_path / "grid.jsonl"
    out.write_text("keep\n", encoding="utf-8")

    assert main(["run", "--out", str(out), "--seeds", "3"]) == 1
    assert out.read_text(encoding="utf-8") == "keep\n"

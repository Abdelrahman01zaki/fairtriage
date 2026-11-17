import pytest

from ai_intelligence_lab.fairtriage.benchmark.grid import file_digest
from ai_intelligence_lab.fairtriage.benchmark.grid_specialty import (
    COMPARISONS,
    GREEDY,
    GREEDY_FIFO,
    OPTIMAL,
    OPTIMAL_FIFO,
    grid_policies,
    grid_specs,
    main,
    run_grid,
    summarize,
)


@pytest.fixture(scope="module")
def records():
    return run_grid(range(2))


def test_every_cell_has_one_specialty_hospital_for_a_quarter_of_casualties():
    for spec in grid_specs().values():
        assert spec.special_hospitals == 1
        assert spec.special_need_share == 0.25


def test_the_four_policies_keep_their_order():
    assert list(grid_policies()) == [GREEDY, GREEDY_FIFO, OPTIMAL, OPTIMAL_FIFO]


def test_every_cell_runs_four_policies_on_every_seed(records):
    seen = {(r.spec_name, r.seed, r.policy_name) for r in records}

    assert len(records) == 36 * 4 * 2
    assert len(seen) == len(records)


def test_summarize_gives_one_row_per_comparison_and_cell(records):
    rows = summarize(records, min_pairs=1)

    assert len(rows) == len(COMPARISONS) * 36
    assert {(row.first, row.second) for row in rows} == set(COMPARISONS)


def test_run_then_summarize_through_the_command_line(tmp_path, capsys):
    out = tmp_path / "runs" / "specialty.jsonl"

    assert main(["run", "--out", str(out), "--seeds", "3"]) == 0
    assert len(out.read_text(encoding="utf-8").splitlines()) == 36 * 4 * 3
    assert main(["summarize", str(out), "--min-pairs", "1"]) == 0

    assert "optimal-greedy | b1_a2_w0" in capsys.readouterr().out


def test_an_existing_output_file_is_not_overwritten(tmp_path):
    out = tmp_path / "specialty.jsonl"
    out.write_text("keep\n", encoding="utf-8")

    assert main(["run", "--out", str(out), "--seeds", "3"]) == 1
    assert out.read_text(encoding="utf-8") == "keep\n"
    assert file_digest(out)

import pytest

from ai_intelligence_lab.fairtriage.benchmark.comparison import (
    category_served_fraction,
    paired_differences,
)
from ai_intelligence_lab.fairtriage.benchmark.records import SCHEMA_VERSION, RunRecord
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.fairness.metrics import CategoryFairness

RED = category_served_fraction(TriageCategory.RED)
BLACK = category_served_fraction(TriageCategory.BLACK)


def record(seed, policy, moved, left, spec="s", spec_hash="h"):
    row = CategoryFairness(TriageCategory.RED, moved, left, None, None, None, 0.0)
    return RunRecord(
        SCHEMA_VERSION, spec, spec_hash, seed, policy, moved, left, 1.0, (row,)
    )


def three_seeds():
    return [
        record(0, "triage", 3, 1),
        record(0, "fifo", 2, 2),
        record(1, "triage", 4, 0),
        record(1, "fifo", 4, 0),
        record(2, "triage", 1, 3),
        record(2, "fifo", 2, 2),
    ]


def test_one_difference_per_seed_in_seed_order():
    shuffled = list(reversed(three_seeds()))

    assert paired_differences(shuffled, "s", "triage", "fifo", RED) == [
        0.25,
        0.0,
        -0.25,
    ]


def test_other_specs_and_policies_are_ignored():
    extra = [record(0, "triage", 0, 4, spec="other"), record(0, "third", 0, 4)]

    found = paired_differences(three_seeds() + extra, "s", "triage", "fifo", RED)

    assert len(found) == 3


def test_a_seed_missing_under_one_policy_is_an_error():
    records = three_seeds()[:-1]

    with pytest.raises(ValueError, match="both policies"):
        paired_differences(records, "s", "triage", "fifo", RED)


def test_a_policy_that_ran_a_seed_twice_is_an_error():
    records = [*three_seeds(), record(1, "fifo", 4, 0)]

    with pytest.raises(ValueError, match="two records"):
        paired_differences(records, "s", "triage", "fifo", RED)


def test_two_specs_under_one_name_are_an_error():
    records = three_seeds()
    records[1] = record(0, "fifo", 2, 2, spec_hash="changed")

    with pytest.raises(ValueError, match="different specs"):
        paired_differences(records, "s", "triage", "fifo", RED)


def test_a_policy_cannot_be_compared_with_itself():
    with pytest.raises(ValueError, match="different"):
        paired_differences(three_seeds(), "s", "triage", "triage", RED)


def test_a_seed_without_the_category_is_left_out():
    assert paired_differences(three_seeds(), "s", "triage", "fifo", BLACK) == []

"""Pair the records of two policies by seed and take one difference per seed.

Both policies ran on the same scenario for each seed, so the difference of a
metric on that seed is a paired difference. The list it returns is what
``paired_summary`` takes.
"""

from collections.abc import Callable, Iterable

from ai_intelligence_lab.fairtriage.benchmark.records import RunRecord
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory

Metric = Callable[[RunRecord], float | None]


def category_served_fraction(category: TriageCategory) -> Metric:
    """Share of ``category``'s casualties that were transported, or None if absent."""

    def measure(record: RunRecord) -> float | None:
        for item in record.categories:
            if item.category is category:
                return item.served_fraction
        return None

    return measure


def paired_differences(
    records: Iterable[RunRecord],
    spec_name: str,
    first: str,
    second: str,
    metric: Metric,
) -> list[float]:
    """``metric`` of ``first`` minus ``metric`` of ``second``, one per seed.

    Seeds come out in increasing order. A seed where either metric is None is
    left out. A seed missing under one policy, a policy that ran a seed twice,
    or two records of one seed from different specs are errors, not gaps.
    """
    if first == second:
        raise ValueError("compare two different policies")

    by_seed: dict[int, dict[str, RunRecord]] = {}
    for record in records:
        if record.spec_name != spec_name:
            continue
        if record.policy_name not in (first, second):
            continue
        slot = by_seed.setdefault(record.seed, {})
        if record.policy_name in slot:
            raise ValueError(
                f"seed {record.seed} has two records for policy {record.policy_name!r}"
            )
        slot[record.policy_name] = record

    differences: list[float] = []
    for seed in sorted(by_seed):
        slot = by_seed[seed]
        if len(slot) != 2:
            raise ValueError(f"seed {seed} was not run under both policies")
        if slot[first].spec_hash != slot[second].spec_hash:
            raise ValueError(f"seed {seed} was run on different specs")
        a, b = metric(slot[first]), metric(slot[second])
        if a is not None and b is not None:
            differences.append(a - b)
    return differences

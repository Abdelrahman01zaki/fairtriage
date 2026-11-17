"""horizon_waits on RunRecord, and the category_horizon_wait metric.

The synthetic-record tests check the metric function in isolation, the same
way test_comparison.py does. The two simulation-based tests check real
properties of horizon_fairness as seen through the runner.
"""

import pytest

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.fairtriage.benchmark.comparison import category_horizon_wait
from ai_intelligence_lab.fairtriage.benchmark.policy import Policy
from ai_intelligence_lab.fairtriage.benchmark.records import SCHEMA_VERSION, RunRecord
from ai_intelligence_lab.fairtriage.benchmark.runner import DEFAULT_HORIZON, run_once
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.fairness.metrics import HorizonWaits
from ai_intelligence_lab.fairtriage.scenarios.generator import ScenarioSpec

_SPEC = ScenarioSpec()
_GREEDY = Policy("greedy", greedy_allocate)


def _record(horizon_waits=()):
    return RunRecord(SCHEMA_VERSION, "s", "h", 1, "p", 0, 0, 1.0, (), horizon_waits)


def test_category_horizon_wait_reads_the_stored_mean():
    waits = (HorizonWaits(TriageCategory.RED, 3, 7.5, 0.1),)

    assert category_horizon_wait(TriageCategory.RED)(_record(waits)) == 7.5


def test_category_horizon_wait_is_none_when_category_is_absent():
    waits = (HorizonWaits(TriageCategory.RED, 3, 7.5, 0.1),)

    assert category_horizon_wait(TriageCategory.BLACK)(_record(waits)) is None


def test_old_records_default_to_no_horizon_waits():
    assert _record().horizon_waits == ()


def test_horizon_waits_cover_every_casualty_not_just_served():
    record = run_once("default", _SPEC, seed=1, policy=_GREEDY)

    assert sum(item.count for item in record.horizon_waits) == _SPEC.casualties


def test_run_once_is_deterministic_with_horizon_waits():
    first = run_once("default", _SPEC, seed=1, policy=_GREEDY)
    second = run_once("default", _SPEC, seed=1, policy=_GREEDY)

    assert first == second


def test_a_horizon_smaller_than_the_report_window_is_rejected():
    with pytest.raises(ValueError, match="horizon"):
        run_once("default", _SPEC, seed=1, policy=_GREEDY, horizon=5.0)


def test_old_records_have_no_recorded_horizon():
    assert _record().horizon == 0.0


def test_run_once_records_the_horizon_it_used():
    default = run_once("default", _SPEC, seed=1, policy=_GREEDY)
    longer = run_once("default", _SPEC, seed=1, policy=_GREEDY, horizon=2000.0)

    assert default.horizon == DEFAULT_HORIZON
    assert longer.horizon == 2000.0


def test_a_negative_horizon_is_rejected():
    with pytest.raises(ValueError, match="horizon"):
        RunRecord(SCHEMA_VERSION, "s", "h", 1, "p", 0, 0, 1.0, (), (), -1.0)

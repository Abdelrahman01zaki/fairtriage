import dataclasses

import pytest

from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.triage.assessment import Assessment
from ai_intelligence_lab.fairtriage.triage.engine import (
    TriageResult,
    triage_casualty,
)
from ai_intelligence_lab.fairtriage.triage.start import StartRule, TriageDecision

RED = TriageCategory.RED
YELLOW = TriageCategory.YELLOW
GREEN = TriageCategory.GREEN
BLACK = TriageCategory.BLACK


def assessment(**overrides):
    """A casualty who cannot walk but shows no urgent sign: YELLOW."""
    fields = {
        "can_walk": False,
        "breaths_per_minute": 20.0,
        "radial_pulse_present": True,
        "capillary_refill_seconds": 1.0,
        "obeys_commands": True,
    }
    fields.update(overrides)
    return Assessment(**fields)


def test_triage_casualty_builds_a_casualty_with_the_decided_category():
    result = triage_casualty("C1", 7.0, assessment(can_walk=True))

    assert result.casualty == Casualty("C1", GREEN, 7.0)
    assert result.decision == TriageDecision(GREEN, StartRule.CAN_WALK)


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"can_walk": True}, GREEN),
        ({"breaths_per_minute": 0.0}, BLACK),
        ({"breaths_per_minute": 40.0}, RED),
        ({}, YELLOW),
    ],
)
def test_casualty_category_always_matches_the_decision(overrides, expected):
    result = triage_casualty("C1", 0.0, assessment(**overrides))

    assert result.casualty.category is expected
    assert result.decision.category is expected


def test_an_empty_id_is_rejected():
    with pytest.raises(ValueError):
        triage_casualty("", 0.0, assessment())


def test_a_negative_report_time_is_rejected():
    with pytest.raises(ValueError):
        triage_casualty("C1", -1.0, assessment())


def test_a_result_whose_category_contradicts_its_decision_is_rejected():
    casualty = Casualty("C1", GREEN, 0.0)
    decision = TriageDecision(RED, StartRule.BREATHING_TOO_FAST)

    with pytest.raises(ValueError):
        TriageResult(casualty, decision)


def test_explain_says_the_category_and_the_rule():
    result = triage_casualty("C1", 0.0, assessment(breaths_per_minute=0.0))

    assert result.explain() == (
        "C1: BLACK because not breathing even after the airway was opened"
    )


def test_result_is_immutable():
    result = triage_casualty("C1", 0.0, assessment())

    with pytest.raises(dataclasses.FrozenInstanceError):
        result.casualty = Casualty("C2", RED, 0.0)


def test_same_observations_give_the_same_result():
    first = triage_casualty("C1", 3.0, assessment(obeys_commands=False))
    second = triage_casualty("C1", 3.0, assessment(obeys_commands=False))

    assert first == second

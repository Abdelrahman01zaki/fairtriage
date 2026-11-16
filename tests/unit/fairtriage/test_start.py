import dataclasses

import pytest

from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.triage.assessment import Assessment
from ai_intelligence_lab.fairtriage.triage.start import (
    StartRule,
    TriageDecision,
    classify,
)

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


CASES = [
    pytest.param({"can_walk": True}, GREEN, StartRule.CAN_WALK, id="walker"),
    pytest.param(
        {"can_walk": True, "breaths_per_minute": 0.0, "radial_pulse_present": False},
        GREEN,
        StartRule.CAN_WALK,
        id="walking_is_decided_first",
    ),
    pytest.param(
        {"breaths_per_minute": 0.0},
        BLACK,
        StartRule.NOT_BREATHING,
        id="not_breathing",
    ),
    pytest.param(
        {"breaths_per_minute": 0.0, "breathes_after_airway_opened": True},
        RED,
        StartRule.BREATHES_AFTER_AIRWAY,
        id="breathes_after_airway",
    ),
    pytest.param(
        {"breaths_per_minute": 31.0},
        RED,
        StartRule.BREATHING_TOO_FAST,
        id="breathing_31",
    ),
    pytest.param(
        {"breaths_per_minute": 30.0},
        YELLOW,
        StartRule.OTHERWISE,
        id="breathing_30_is_not_too_fast",
    ),
    pytest.param(
        {"radial_pulse_present": False},
        RED,
        StartRule.POOR_CIRCULATION,
        id="no_pulse",
    ),
    pytest.param(
        {"capillary_refill_seconds": 2.5},
        RED,
        StartRule.POOR_CIRCULATION,
        id="slow_refill",
    ),
    pytest.param(
        {"capillary_refill_seconds": 2.0},
        YELLOW,
        StartRule.OTHERWISE,
        id="refill_2_is_not_too_slow",
    ),
    pytest.param(
        {"obeys_commands": False},
        RED,
        StartRule.CANNOT_FOLLOW_COMMANDS,
        id="cannot_follow_commands",
    ),
    pytest.param({}, YELLOW, StartRule.OTHERWISE, id="no_urgent_sign"),
    pytest.param(
        {"breaths_per_minute": 0.0, "radial_pulse_present": False},
        BLACK,
        StartRule.NOT_BREATHING,
        id="breathing_is_checked_before_circulation",
    ),
    pytest.param(
        {"breaths_per_minute": 40.0, "obeys_commands": False},
        RED,
        StartRule.BREATHING_TOO_FAST,
        id="breathing_is_checked_before_commands",
    ),
    pytest.param(
        {"radial_pulse_present": False, "obeys_commands": False},
        RED,
        StartRule.POOR_CIRCULATION,
        id="circulation_is_checked_before_commands",
    ),
]


@pytest.mark.parametrize(("overrides", "category", "rule"), CASES)
def test_classify_gives_the_expected_category_and_rule(overrides, category, rule):
    decision = classify(assessment(**overrides))

    assert decision == TriageDecision(category, rule)


def test_every_rule_is_covered_by_at_least_one_case():
    covered = {case.values[2] for case in CASES}

    assert covered == set(StartRule)


def test_decision_is_immutable():
    decision = classify(assessment())

    with pytest.raises(dataclasses.FrozenInstanceError):
        decision.category = GREEN

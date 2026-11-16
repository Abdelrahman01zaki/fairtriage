import dataclasses
import math

import pytest

from ai_intelligence_lab.fairtriage.triage.assessment import Assessment


def assessment(**overrides):
    fields = {
        "can_walk": False,
        "breaths_per_minute": 20.0,
        "radial_pulse_present": True,
        "capillary_refill_seconds": 1.0,
        "obeys_commands": True,
    }
    fields.update(overrides)
    return Assessment(**fields)


def test_valid_assessment_keeps_its_fields():
    item = assessment(can_walk=True, breaths_per_minute=18.0)

    assert item.can_walk is True
    assert item.breaths_per_minute == 18.0
    assert item.radial_pulse_present is True
    assert item.capillary_refill_seconds == 1.0
    assert item.obeys_commands is True


def test_airway_flag_defaults_to_false():
    assert assessment().breathes_after_airway_opened is False


@pytest.mark.parametrize("bad_rate", [-1.0, math.nan, math.inf])
def test_breathing_rate_must_be_finite_and_not_negative(bad_rate):
    with pytest.raises(ValueError):
        assessment(breaths_per_minute=bad_rate)


@pytest.mark.parametrize("bad_refill", [-0.5, math.nan, math.inf])
def test_capillary_refill_must_be_finite_and_not_negative(bad_refill):
    with pytest.raises(ValueError):
        assessment(capillary_refill_seconds=bad_refill)


def test_a_rate_of_zero_means_not_breathing_and_is_allowed():
    assert assessment(breaths_per_minute=0.0).breaths_per_minute == 0.0


def test_airway_flag_is_allowed_for_a_casualty_who_is_not_breathing():
    item = assessment(breaths_per_minute=0.0, breathes_after_airway_opened=True)

    assert item.breathes_after_airway_opened is True


def test_airway_flag_is_rejected_for_a_casualty_who_is_breathing():
    # Contradiction: if they were already breathing, no airway step was needed.
    with pytest.raises(ValueError):
        assessment(breaths_per_minute=20.0, breathes_after_airway_opened=True)


def test_assessment_is_immutable():
    item = assessment()

    with pytest.raises(dataclasses.FrozenInstanceError):
        item.can_walk = True

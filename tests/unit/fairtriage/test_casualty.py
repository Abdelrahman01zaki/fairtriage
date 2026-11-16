import dataclasses
import math

import pytest

from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory

RED = TriageCategory.RED


def casualty(casualty_id="C1", category=RED, reported_at=5.0):
    return Casualty(casualty_id, category, reported_at)


def test_valid_casualty_keeps_its_fields():
    item = casualty("C7", TriageCategory.YELLOW, 12.5)

    assert item.id == "C7"
    assert item.category is TriageCategory.YELLOW
    assert item.reported_at == 12.5


def test_casualty_needs_an_id():
    with pytest.raises(ValueError):
        casualty(casualty_id="")


def test_category_must_be_a_triage_category():
    # "RED" as plain text would silently pass as a label and break sorting later.
    with pytest.raises(ValueError):
        casualty(category="RED")


@pytest.mark.parametrize("bad_time", [-1.0, math.nan, math.inf])
def test_reported_time_must_be_finite_and_not_negative(bad_time):
    with pytest.raises(ValueError):
        casualty(reported_at=bad_time)


def test_waited_is_the_time_since_the_casualty_was_reported():
    assert casualty(reported_at=5.0).waited(20.0) == 15.0


def test_waited_is_zero_at_the_moment_of_reporting():
    assert casualty(reported_at=5.0).waited(5.0) == 0.0


def test_waited_rejects_a_time_before_the_report():
    with pytest.raises(ValueError):
        casualty(reported_at=5.0).waited(4.0)


def test_casualty_is_immutable():
    item = casualty()

    with pytest.raises(dataclasses.FrozenInstanceError):
        item.category = TriageCategory.GREEN


def test_equal_casualties_are_the_same_key():
    assert casualty() == casualty()
    assert len({casualty(), casualty(), casualty("C2")}) == 2

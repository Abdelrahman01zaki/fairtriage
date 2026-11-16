import pytest

from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory


def make(**overrides):
    parts = {"id": "C-1", "category": TriageCategory.RED, "reported_at": 0.0}
    parts.update(overrides)
    return Casualty(**parts)


def test_a_casualty_needs_no_specialty_by_default():
    assert make().needs == frozenset()


def test_needs_can_be_given_as_any_collection_and_are_frozen():
    casualty = make(needs=["burns", "trauma"])

    assert casualty.needs == frozenset({"burns", "trauma"})
    assert isinstance(casualty.needs, frozenset)


def test_the_order_of_needs_does_not_matter():
    assert make(needs=["burns", "trauma"]) == make(needs=("trauma", "burns"))


def test_needs_given_as_a_single_string_are_rejected():
    with pytest.raises(ValueError):
        make(needs="burns")


def test_a_casualty_with_needs_can_still_be_hashed():
    assert len({make(needs=["burns"]), make(needs=["burns"])}) == 1

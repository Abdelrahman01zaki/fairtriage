import dataclasses

import pytest

from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory

RED = TriageCategory.RED
YELLOW = TriageCategory.YELLOW
GREEN = TriageCategory.GREEN


def casualty(casualty_id, category=RED, reported_at=0.0):
    return Casualty(casualty_id, category, reported_at)


def incident(incident_id="I1", location="N1", casualties=None):
    if casualties is None:
        casualties = (casualty("C1"), casualty("C2", YELLOW))
    return Incident(incident_id, location, casualties)


def test_valid_incident_keeps_its_fields_and_order():
    item = incident()

    assert item.id == "I1"
    assert item.location == "N1"
    assert [c.id for c in item.casualties] == ["C1", "C2"]


def test_incident_needs_an_id_and_a_location():
    with pytest.raises(ValueError):
        incident(incident_id="")
    with pytest.raises(ValueError):
        incident(location="")


def test_incident_needs_at_least_one_casualty():
    with pytest.raises(ValueError):
        incident(casualties=())


def test_duplicate_casualty_ids_are_rejected():
    # Almost always a typo, and it would make two people look like one.
    with pytest.raises(ValueError):
        incident(casualties=(casualty("C1"), casualty("C1", YELLOW)))


def test_every_casualty_must_be_a_casualty():
    with pytest.raises(ValueError):
        incident(casualties=(casualty("C1"), "C2"))


def test_casualties_reject_a_bare_string():
    with pytest.raises(ValueError):
        incident(casualties="C1")


def test_casualties_are_copied_into_a_tuple():
    given = [casualty("C1")]
    item = incident(casualties=given)

    given.append(casualty("C2"))  # changing the caller's list must not change it

    assert item.casualties == (casualty("C1"),)
    assert isinstance(item.casualties, tuple)


def test_in_category_returns_matching_casualties_in_order():
    item = incident(
        casualties=(casualty("C1", RED), casualty("C2", YELLOW), casualty("C3", RED))
    )

    assert [c.id for c in item.in_category(RED)] == ["C1", "C3"]


def test_in_category_is_empty_when_nobody_matches():
    item = incident(casualties=(casualty("C1", RED),))

    assert item.in_category(GREEN) == ()


def test_incident_is_immutable():
    item = incident()

    with pytest.raises(dataclasses.FrozenInstanceError):
        item.location = "N2"

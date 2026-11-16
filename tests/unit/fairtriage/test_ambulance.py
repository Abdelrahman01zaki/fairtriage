import dataclasses

import pytest

from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance


def test_valid_ambulance_keeps_its_fields():
    item = Ambulance("A1", "Station1")

    assert item.id == "A1"
    assert item.base == "Station1"


def test_ambulance_needs_an_id_and_a_base():
    with pytest.raises(ValueError):
        Ambulance("", "Station1")
    with pytest.raises(ValueError):
        Ambulance("A1", "")


def test_ambulance_is_immutable():
    item = Ambulance("A1", "Station1")

    with pytest.raises(dataclasses.FrozenInstanceError):
        item.base = "Station2"


def test_equal_ambulances_are_the_same_key():
    assert Ambulance("A1", "S1") == Ambulance("A1", "S1")
    assert (
        len({Ambulance("A1", "S1"), Ambulance("A1", "S1"), Ambulance("A2", "S1")}) == 2
    )

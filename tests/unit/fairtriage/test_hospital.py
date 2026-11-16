import dataclasses

import pytest

from ai_intelligence_lab.fairtriage.domain.hospital import Hospital


def hospital(hospital_id="H1", location="N1", beds=50, specialties=()):
    return Hospital(hospital_id, location, beds, frozenset(specialties))


def test_valid_hospital_keeps_its_fields():
    item = Hospital("H1", "N1", 50, frozenset({"trauma"}))

    assert item.id == "H1"
    assert item.location == "N1"
    assert item.beds == 50
    assert item.specialties == frozenset({"trauma"})


def test_specialties_are_optional():
    assert Hospital("H1", "N1", 50).specialties == frozenset()


def test_hospital_needs_an_id_and_a_location():
    with pytest.raises(ValueError):
        hospital(hospital_id="")
    with pytest.raises(ValueError):
        hospital(location="")


@pytest.mark.parametrize("bad_beds", [0, -3])
def test_hospital_needs_a_positive_number_of_beds(bad_beds):
    with pytest.raises(ValueError):
        hospital(beds=bad_beds)


def test_specialties_are_copied_into_a_frozenset():
    given = {"trauma", "burns"}
    item = Hospital("H1", "N1", 50, given)

    given.add("cardiac")  # changing the caller's set must not change the hospital

    assert item.specialties == frozenset({"trauma", "burns"})
    assert isinstance(item.specialties, frozenset)


def test_specialties_reject_a_bare_string():
    # "trauma" would silently become {"t", "r", "a", ...}.
    with pytest.raises(ValueError):
        Hospital("H1", "N1", 50, "trauma")


def test_hospital_is_immutable():
    item = hospital()

    with pytest.raises(dataclasses.FrozenInstanceError):
        item.beds = 5

import pytest

from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.simulation.state import (
    AmbulanceStatus,
    WorldState,
)


def make_state() -> WorldState:
    return WorldState.start(
        [Ambulance("A1", "base1"), Ambulance("A2", "base2")],
        [Hospital("H1", "hosp1", beds=2), Hospital("H2", "hosp2", beds=1)],
    )


def test_at_the_start_every_ambulance_is_free_at_its_base():
    state = make_state()

    for status in state.ambulances:
        assert status.location == status.ambulance.base
        assert status.free_at == 0.0


def test_at_the_start_no_bed_is_taken():
    state = make_state()

    assert state.free_beds("H1") == 2
    assert state.free_beds("H2") == 1


def test_moving_an_ambulance_gives_a_new_state_and_keeps_the_old_one():
    before = make_state()
    after = before.with_ambulance("A1", "hosp1", 12.5)

    assert after.status_of("A1").location == "hosp1"
    assert after.status_of("A1").free_at == 12.5
    assert after.status_of("A2") == before.status_of("A2")
    assert before.status_of("A1").location == "base1"


def test_a_busy_ambulance_is_not_available_until_it_is_free():
    state = make_state().with_ambulance("A1", "hosp1", 10.0)

    assert [a.id for a in state.available_ambulances(9.9)] == ["A2"]
    assert [a.id for a in state.available_ambulances(10.0)] == ["A1", "A2"]


def test_an_available_ambulance_is_described_by_where_it_is_now():
    state = make_state().with_ambulance("A1", "hosp1", 0.0)

    available = {a.id: a.base for a in state.available_ambulances(0.0)}

    assert available == {"A1": "hosp1", "A2": "base2"}


def test_an_admission_takes_a_bed_and_keeps_the_old_state():
    before = make_state()
    after = before.with_admission("H1")

    assert after.free_beds("H1") == 1
    assert after.free_beds("H2") == 1
    assert before.free_beds("H1") == 2


def test_a_full_hospital_cannot_admit():
    state = make_state().with_admission("H2")

    with pytest.raises(ValueError):
        state.with_admission("H2")


def test_unknown_names_are_rejected():
    state = make_state()

    with pytest.raises(ValueError):
        state.status_of("nobody")
    with pytest.raises(ValueError):
        state.free_beds("nowhere")
    with pytest.raises(ValueError):
        state.with_ambulance("nobody", "x", 1.0)
    with pytest.raises(ValueError):
        state.with_admission("nowhere")


def test_duplicate_ids_are_rejected():
    with pytest.raises(ValueError):
        WorldState.start([Ambulance("A", "b1"), Ambulance("A", "b2")], [])
    with pytest.raises(ValueError):
        WorldState.start([], [Hospital("H", "x", 1), Hospital("H", "y", 1)])


def test_beds_taken_must_fit_the_hospital():
    hospital = Hospital("H1", "hosp1", beds=2)

    with pytest.raises(ValueError):
        WorldState((), (hospital,), {"H1": 3})
    with pytest.raises(ValueError):
        WorldState((), (hospital,), {"H1": -1})
    with pytest.raises(ValueError):
        WorldState((), (hospital,), {"H9": 1})


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0])
def test_a_bad_free_time_is_rejected(bad):
    with pytest.raises(ValueError):
        AmbulanceStatus(Ambulance("A1", "base1"), "base1", bad)


def test_an_ambulance_needs_a_location():
    with pytest.raises(ValueError):
        AmbulanceStatus(Ambulance("A1", "base1"), "")

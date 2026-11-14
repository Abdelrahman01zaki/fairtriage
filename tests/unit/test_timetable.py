import dataclasses

import pytest

from ai_intelligence_lab.environments.timetable import Lecture, Period, Room, Timetable

SAT1, SAT2 = Period("Sat", 1), Period("Sat", 2)


def lecture(lecture_id="L1", teacher="T1", curricula=("Y1",), students=30):
    return Lecture(lecture_id, teacher, frozenset(curricula), students)


def make_timetable(**overrides):
    parts = {
        "lectures": (lecture("L1"), lecture("L2", teacher="T2")),
        "rooms": (Room("R1", 40), Room("R2", 100)),
        "periods": (SAT1, SAT2),
    }
    parts.update(overrides)
    return Timetable(**parts)


# --- Period -------------------------------------------------------------


def test_period_prints_as_day_and_slot():
    assert str(Period("Sat", 1)) == "Sat 1"


def test_equal_periods_are_the_same_key():
    assert Period("Sat", 1) == Period("Sat", 1)
    assert len({Period("Sat", 1), Period("Sat", 1), Period("Sat", 2)}) == 2


def test_period_rejects_empty_day_and_bad_slot():
    with pytest.raises(ValueError):
        Period("", 1)
    with pytest.raises(ValueError):
        Period("Sat", 0)


# --- Room and Lecture ----------------------------------------------------


def test_room_rejects_empty_name_and_non_positive_capacity():
    with pytest.raises(ValueError):
        Room("", 10)
    with pytest.raises(ValueError):
        Room("R1", 0)


def test_lecture_rejects_missing_fields():
    with pytest.raises(ValueError):
        lecture(lecture_id="")
    with pytest.raises(ValueError):
        lecture(teacher="")
    with pytest.raises(ValueError):
        lecture(students=0)


def test_lecture_curricula_are_copied_into_a_frozenset():
    groups = {"Y1", "Y2"}
    item = Lecture("L1", "T1", groups, 30)

    groups.add("Y3")  # changing the caller's set must not change the lecture

    assert item.curricula == frozenset({"Y1", "Y2"})
    assert isinstance(item.curricula, frozenset)


def test_lecture_rejects_a_bare_string_as_curricula():
    # "Y1" would silently become {"Y", "1"}, which is never what anyone meant.
    with pytest.raises(ValueError):
        Lecture("L1", "T1", "Y1", 30)


# --- Timetable ----------------------------------------------------------


def test_valid_timetable_keeps_its_parts_in_order():
    timetable = make_timetable()

    assert [item.id for item in timetable.lectures] == ["L1", "L2"]
    assert [room.name for room in timetable.rooms] == ["R1", "R2"]
    assert timetable.periods == (SAT1, SAT2)
    assert dict(timetable.unavailable) == {}


def test_timetable_needs_lectures_rooms_and_periods():
    with pytest.raises(ValueError):
        make_timetable(lectures=())
    with pytest.raises(ValueError):
        make_timetable(rooms=())
    with pytest.raises(ValueError):
        make_timetable(periods=())


def test_timetable_rejects_duplicates():
    with pytest.raises(ValueError):
        make_timetable(lectures=(lecture("L1"), lecture("L1")))
    with pytest.raises(ValueError):
        make_timetable(rooms=(Room("R1", 40), Room("R1", 80)))
    with pytest.raises(ValueError):
        make_timetable(periods=(SAT1, SAT1))


def test_unavailability_for_an_unknown_teacher_is_rejected():
    # Almost always a typo in the teacher's name.
    with pytest.raises(ValueError):
        make_timetable(unavailable={"T9": {SAT1}})


def test_unavailability_at_an_unknown_period_is_rejected():
    with pytest.raises(ValueError):
        make_timetable(unavailable={"T1": {Period("Sun", 1)}})


def test_unavailability_is_copied_and_frozen():
    blocked = {SAT1}
    original = {"T1": blocked}
    timetable = make_timetable(unavailable=original)

    blocked.add(SAT2)
    original["T2"] = {SAT2}

    assert dict(timetable.unavailable) == {"T1": frozenset({SAT1})}
    with pytest.raises(TypeError):
        timetable.unavailable["T1"] = frozenset()


def test_timetable_is_immutable():
    timetable = make_timetable()

    with pytest.raises(dataclasses.FrozenInstanceError):
        timetable.rooms = ()

import pytest

from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.simulation.repositioning import (
    POLICIES,
    RepositionContext,
    adaptive,
    return_to_base,
    stay_at_hospital,
)


def context(pending: int) -> RepositionContext:
    return RepositionContext(Ambulance("A1", "base1"), "hosp1", pending)


def test_return_to_base_always_goes_home():
    assert return_to_base(context(0)) == "base1"
    assert return_to_base(context(5)) == "base1"


def test_stay_at_hospital_never_moves():
    assert stay_at_hospital(context(0)) == "hosp1"
    assert stay_at_hospital(context(5)) == "hosp1"


def test_adaptive_stays_while_casualties_wait():
    assert adaptive(context(3)) == "hosp1"


def test_adaptive_returns_to_base_when_nobody_waits():
    assert adaptive(context(0)) == "base1"


def test_every_policy_is_listed_by_name():
    assert set(POLICIES) == {"return_to_base", "stay_at_hospital", "adaptive"}
    assert POLICIES["adaptive"] is adaptive


def test_a_context_needs_a_place_and_a_valid_count():
    with pytest.raises(ValueError):
        RepositionContext(Ambulance("A1", "base1"), "", 0)
    with pytest.raises(ValueError):
        RepositionContext(Ambulance("A1", "base1"), "hosp1", -1)

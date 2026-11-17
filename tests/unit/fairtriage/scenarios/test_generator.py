import os
import subprocess
import sys

import pytest

from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.scenarios.generator import (
    ScenarioSpec,
    generate_scenario,
)
from ai_intelligence_lab.fairtriage.simulation.engine import simulate

RED = TriageCategory.RED
YELLOW = TriageCategory.YELLOW
GREEN = TriageCategory.GREEN
BLACK = TriageCategory.BLACK

SPEC = ScenarioSpec()


def _reachable(scenario):
    network = scenario.network
    start = network.junctions[0].id
    seen = {start}
    stack = [start]
    while stack:
        here = stack.pop()
        for there in network.neighbors(here):
            if there not in seen:
                seen.add(there)
                stack.append(there)
    return seen


def test_same_seed_gives_the_same_scenario():
    assert generate_scenario(SPEC, seed=7) == generate_scenario(SPEC, seed=7)


def test_different_seeds_give_different_scenarios():
    assert generate_scenario(SPEC, seed=1) != generate_scenario(SPEC, seed=2)


def test_counts_follow_the_spec():
    spec = ScenarioSpec(
        casualties=20,
        hospitals=4,
        beds_per_hospital=2,
        ambulances=5,
        junctions=10,
        extra_roads=2,
    )

    scenario = generate_scenario(spec, seed=3)

    assert len(scenario.incident.casualties) == 20
    assert len(scenario.hospitals) == 4
    assert all(hospital.beds == 2 for hospital in scenario.hospitals)
    assert len(scenario.ambulances) == 5
    assert len(scenario.network.junctions) == 10


def test_roads_are_a_spanning_tree_plus_the_extra_roads():
    spec = ScenarioSpec(junctions=9, extra_roads=4)

    for seed in range(10):
        assert len(generate_scenario(spec, seed=seed).network.roads) == 9 - 1 + 4


def test_the_network_is_always_connected():
    for seed in range(30):
        scenario = generate_scenario(SPEC, seed=seed)

        assert _reachable(scenario) == {j.id for j in scenario.network.junctions}


def test_report_times_stay_inside_the_window():
    spec = ScenarioSpec(casualties=30, report_window=12.0)

    for seed in range(10):
        casualties = generate_scenario(spec, seed=seed).incident.casualties

        assert all(0.0 <= item.reported_at <= 12.0 for item in casualties)


def test_a_zero_window_reports_everyone_at_minute_zero():
    spec = ScenarioSpec(report_window=0.0)

    casualties = generate_scenario(spec, seed=1).incident.casualties

    assert {item.reported_at for item in casualties} == {0.0}


def test_a_category_with_zero_weight_never_appears():
    spec = ScenarioSpec(
        casualties=40,
        category_weights=((RED, 1.0), (YELLOW, 1.0), (GREEN, 1.0), (BLACK, 0.0)),
    )

    for seed in range(10):
        incident = generate_scenario(spec, seed=seed).incident

        assert incident.in_category(BLACK) == ()


def test_every_generated_scenario_can_be_simulated():
    for seed in range(20):
        scenario = generate_scenario(SPEC, seed=seed)

        result = simulate(scenario)

        served = len(result.transports) + len(result.unserved)
        assert served == len(scenario.incident.casualties)


@pytest.mark.parametrize(
    "changes",
    [
        {"casualties": 0},
        {"hospitals": 0},
        {"beds_per_hospital": 0},
        {"ambulances": 0},
        {"junctions": 1},
        {"extra_roads": -1},
        {"extra_roads": 100},
        {"report_window": -1.0},
        {"report_window": float("inf")},
        {"category_weights": ()},
        {"category_weights": ((RED, 0.0), (GREEN, 0.0))},
        {"category_weights": ((RED, -1.0), (GREEN, 2.0))},
        {"category_weights": ((RED, 1.0), (RED, 2.0))},
        {"special_hospitals": -1},
        {"special_hospitals": 4},
        {"special_need_share": -0.1},
        {"special_need_share": 1.1},
        {"special_need_share": float("nan")},
        {"special_need_share": float("inf")},
        {"special_need_share": 0.5},
    ],
)
def test_a_bad_spec_is_rejected(changes):
    with pytest.raises(ValueError):
        ScenarioSpec(**changes)


def test_the_result_does_not_depend_on_python_hash_randomization():
    code = (
        "from ai_intelligence_lab.fairtriage.scenarios.generator import "
        "ScenarioSpec, generate_scenario\n"
        "spec = ScenarioSpec(special_hospitals=1, special_need_share=0.5)\n"
        "print(generate_scenario(ScenarioSpec(), seed=3))\n"
        "print(generate_scenario(spec, seed=3))"
    )
    outputs = []
    for hash_seed in ("1", "2"):
        env = {**os.environ, "PYTHONHASHSEED": hash_seed}
        done = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        outputs.append(done.stdout)

    assert outputs[0]
    assert outputs[0] == outputs[1]


def test_by_default_nobody_needs_a_specialty_and_no_hospital_offers_one():
    for seed in range(10):
        scenario = generate_scenario(SPEC, seed=seed)

        assert all(item.needs == frozenset() for item in scenario.incident.casualties)
        assert all(item.specialties == frozenset() for item in scenario.hospitals)


def test_the_requested_number_of_hospitals_offer_the_specialty():
    spec = ScenarioSpec(hospitals=4, special_hospitals=2, special_need_share=0.5)

    for seed in range(10):
        hospitals = generate_scenario(spec, seed=seed).hospitals
        special = [item for item in hospitals if item.specialties]

        assert len(special) == 2
        assert all(item.specialties == frozenset({"burns"}) for item in special)


def test_the_need_share_sets_who_needs_the_specialty():
    everyone = ScenarioSpec(casualties=30, special_hospitals=1, special_need_share=1.0)
    nobody = ScenarioSpec(casualties=30, special_hospitals=1, special_need_share=0.0)
    some = ScenarioSpec(casualties=40, special_hospitals=1, special_need_share=0.5)

    burns = frozenset({"burns"})
    all_needs = generate_scenario(everyone, seed=1).incident.casualties
    none_needs = generate_scenario(nobody, seed=1).incident.casualties
    mixed = {item.needs for item in generate_scenario(some, seed=1).incident.casualties}

    assert all(item.needs == burns for item in all_needs)
    assert all(item.needs == frozenset() for item in none_needs)
    assert mixed == {burns, frozenset()}


def test_turning_needs_on_changes_nothing_else_about_the_scenario():
    plain = ScenarioSpec()
    with_needs = ScenarioSpec(special_hospitals=1, special_need_share=0.5)

    for seed in range(20):
        a = generate_scenario(plain, seed=seed)
        b = generate_scenario(with_needs, seed=seed)

        assert a.network == b.network
        assert a.ambulances == b.ambulances
        assert a.incident.location == b.incident.location
        assert [(h.id, h.location, h.beds) for h in a.hospitals] == [
            (h.id, h.location, h.beds) for h in b.hospitals
        ]
        assert [(c.id, c.category, c.reported_at) for c in a.incident.casualties] == [
            (c.id, c.category, c.reported_at) for c in b.incident.casualties
        ]

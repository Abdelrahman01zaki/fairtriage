import json

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.optimal import optimal_allocate
from ai_intelligence_lab.fairtriage.benchmark.policy import Policy
from ai_intelligence_lab.fairtriage.benchmark.records import spec_hash, to_json_dict
from ai_intelligence_lab.fairtriage.benchmark.runner import (
    Experiment,
    run_experiment,
    run_once,
)
from ai_intelligence_lab.fairtriage.scenarios.generator import ScenarioSpec

# 6 casualties, 2 hospitals with 1 bed each: real scarcity (2 beds for 6).
_SCARCE = ScenarioSpec(
    casualties=6,
    hospitals=2,
    beds_per_hospital=1,
    ambulances=2,
    junctions=4,
    extra_roads=0,
)
_GREEDY = Policy("greedy", greedy_allocate)
_OPTIMAL = Policy("optimal", optimal_allocate)


def test_run_once_is_deterministic():
    first = run_once("scarce", _SCARCE, seed=1, policy=_GREEDY)
    second = run_once("scarce", _SCARCE, seed=1, policy=_GREEDY)
    assert first == second


def test_served_and_unserved_cover_every_casualty():
    record = run_once("scarce", _SCARCE, seed=1, policy=_GREEDY)
    assert record.served + record.unserved_total == _SCARCE.casualties


def test_spec_hash_is_stable_and_distinguishes_specs():
    other = ScenarioSpec(
        casualties=6,
        hospitals=2,
        beds_per_hospital=2,
        ambulances=2,
        junctions=4,
        extra_roads=0,
    )
    assert spec_hash(_SCARCE) == spec_hash(_SCARCE)
    assert spec_hash(_SCARCE) != spec_hash(other)


def test_record_is_json_serializable():
    record = run_once("scarce", _SCARCE, seed=1, policy=_GREEDY)
    encoded = json.dumps(to_json_dict(record))
    decoded = json.loads(encoded)
    assert decoded["spec_name"] == "scarce"
    assert decoded["policy_name"] == "greedy"
    assert isinstance(decoded["categories"], list)


def test_run_experiment_covers_every_combination():
    experiment = Experiment(
        specs={"scarce": _SCARCE},
        seeds=(1, 2, 3),
        policies={"greedy": _GREEDY, "optimal": _OPTIMAL},
    )
    records = run_experiment(experiment)
    assert len(records) == 1 * 3 * 2
    seen = {(r.spec_name, r.seed, r.policy_name) for r in records}
    assert seen == {
        ("scarce", seed, policy)
        for seed in (1, 2, 3)
        for policy in ("greedy", "optimal")
    }


def test_experiment_rejects_empty_inputs():
    import pytest

    with pytest.raises(ValueError, match="spec"):
        Experiment(specs={}, seeds=(1,), policies={"greedy": _GREEDY})

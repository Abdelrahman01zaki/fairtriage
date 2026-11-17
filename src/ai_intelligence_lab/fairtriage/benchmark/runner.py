"""Run one or many (spec, seed, policy) combinations and collect RunRecords.

Each run is a pure function of (spec, seed, policy): same inputs, same
record. That is what will let a later version resume, cache or parallelize
runs without changing this module.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ai_intelligence_lab.fairtriage.benchmark.policy import Policy
from ai_intelligence_lab.fairtriage.benchmark.records import (
    SCHEMA_VERSION,
    RunRecord,
    spec_hash,
)
from ai_intelligence_lab.fairtriage.fairness.metrics import fairness_report
from ai_intelligence_lab.fairtriage.scenarios.generator import (
    ScenarioSpec,
    generate_scenario,
)
from ai_intelligence_lab.fairtriage.simulation.engine import simulate


def run_once(
    spec_name: str, spec: ScenarioSpec, seed: int, policy: Policy
) -> RunRecord:
    """Generate one scenario and run one policy on it."""
    scenario = generate_scenario(spec, seed=seed)
    result = simulate(
        scenario, allocator=policy.allocator, repositioning=policy.repositioning
    )
    report = fairness_report(scenario.incident, result)
    return RunRecord(
        SCHEMA_VERSION,
        spec_name,
        spec_hash(spec),
        seed,
        policy.name,
        len(result.transports),
        len(result.unserved),
        result.end_time,
        report.categories,
    )


@dataclass(frozen=True, slots=True)
class Experiment:
    """Every (spec, seed, policy) combination to run.

    ``specs`` names each spec, so the name becomes the stratum later when
    results are grouped for statistics (for example "beds_1", "beds_2").
    """

    specs: Mapping[str, ScenarioSpec]
    seeds: tuple[int, ...]
    policies: Mapping[str, Policy]

    def __post_init__(self) -> None:
        if not self.specs:
            raise ValueError("an experiment needs at least one spec")
        if not self.seeds:
            raise ValueError("an experiment needs at least one seed")
        if not self.policies:
            raise ValueError("an experiment needs at least one policy")
        object.__setattr__(self, "specs", MappingProxyType(dict(self.specs)))
        object.__setattr__(self, "seeds", tuple(self.seeds))
        object.__setattr__(self, "policies", MappingProxyType(dict(self.policies)))


def run_experiment(experiment: Experiment) -> tuple[RunRecord, ...]:
    """Every record of ``experiment``, in spec, then seed, then policy order."""
    records = [
        run_once(spec_name, spec, seed, policy)
        for spec_name, spec in experiment.specs.items()
        for seed in experiment.seeds
        for policy in experiment.policies.values()
    ]
    return tuple(records)

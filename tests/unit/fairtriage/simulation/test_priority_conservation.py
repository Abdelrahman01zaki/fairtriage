"""The priority rule moves waiting between categories; it does not remove it.

Without a specialty need, when each ambulance is sent and how long each trip
takes do not depend on which casualty rides, so the total wait of all casualties
is the same under any priority rule. A specialty need breaks this: the hospital a
casualty must go to changes the trip, so the rule can change the total.

These are small checks on generated scenarios, not a proof.
"""

import pytest

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.optimal import optimal_allocate
from ai_intelligence_lab.fairtriage.fairness.metrics import waits_to_horizon
from ai_intelligence_lab.fairtriage.scenarios.generator import (
    ScenarioSpec,
    generate_scenario,
)
from ai_intelligence_lab.fairtriage.simulation.engine import simulate
from ai_intelligence_lab.fairtriage.transport.priority import by_urgency, fifo

HORIZON = 1000.0
SEEDS = range(30)
ALLOCATORS = {"greedy": greedy_allocate, "optimal": optimal_allocate}
SPECS = {
    "everyone_waits_together": ScenarioSpec(report_window=0.0),
    "reports_spread_out": ScenarioSpec(report_window=60.0),
    "many_ambulances": ScenarioSpec(ambulances=6, report_window=60.0),
    "scarce_beds": ScenarioSpec(beds_per_hospital=2, report_window=60.0),
}
SPECIAL = ScenarioSpec(special_hospitals=1, special_need_share=0.25)


def total_wait(scenario, allocator, rule):
    result = simulate(scenario, allocator=allocator, priority=rule)
    waits = waits_to_horizon(scenario.incident, result, HORIZON)
    return sum(sum(values) for values in waits.values())


def gaps(spec, allocator):
    found = []
    for seed in SEEDS:
        scenario = generate_scenario(spec, seed=seed)
        triage = total_wait(scenario, allocator, by_urgency)
        first_come = total_wait(scenario, allocator, fifo)
        found.append(abs(triage - first_come))
    return found


@pytest.mark.parametrize("allocator", ALLOCATORS)
@pytest.mark.parametrize("spec", SPECS)
def test_total_wait_is_the_same_under_any_rule(spec, allocator):
    assert max(gaps(SPECS[spec], ALLOCATORS[allocator])) < 1e-6


@pytest.mark.parametrize("allocator", ALLOCATORS)
def test_a_specialty_need_lets_the_rule_change_the_total_wait(allocator):
    assert max(gaps(SPECIAL, ALLOCATORS[allocator])) > 1e-6

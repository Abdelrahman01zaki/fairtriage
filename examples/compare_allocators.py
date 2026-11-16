"""Compare allocators on one incident where the only burns unit is contested.

Run it from the project root:  python examples/compare_allocators.py
"""

from ai_intelligence_lab.allocation.greedy import greedy_allocate
from ai_intelligence_lab.allocation.model import Allocator
from ai_intelligence_lab.allocation.optimal import optimal_allocate
from ai_intelligence_lab.environments.road_network import Junction, Road, RoadNetwork
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.fairness.metrics import fairness_report
from ai_intelligence_lab.fairtriage.simulation.engine import simulate
from ai_intelligence_lab.fairtriage.simulation.scenario import Scenario

RED = TriageCategory.RED
YELLOW = TriageCategory.YELLOW
GREEN = TriageCategory.GREEN
BURNS = frozenset({"burns"})

NETWORK = RoadNetwork(
    (
        Junction("BASE", 0.0, 0.0),
        Junction("SCENE", 2.0, 0.0),
        Junction("BURNS", 6.0, 0.0),
        Junction("GENERAL", 2.0, 10.0),
    ),
    (
        Road("BASE", "SCENE", 2.0),
        Road("SCENE", "BURNS", 4.0),
        Road("SCENE", "GENERAL", 10.0),
    ),
)

INCIDENT = Incident(
    "BURNS-DEMO",
    "SCENE",
    (
        Casualty("R1", RED, 0.0),
        Casualty("R2", RED, 0.0),
        Casualty("Y1", YELLOW, 0.0, BURNS),
        Casualty("Y2", YELLOW, 0.0, BURNS),
        Casualty("G1", GREEN, 0.0),
        Casualty("G2", GREEN, 0.0),
    ),
)

SCENARIO = Scenario(
    NETWORK,
    INCIDENT,
    (
        Hospital("H-burns", "BURNS", 2, BURNS),
        Hospital("H-general", "GENERAL", 3),
    ),
    (Ambulance("A1", "BASE"), Ambulance("A2", "BASE"), Ambulance("A3", "BASE")),
)

ALLOCATORS: dict[str, Allocator] = {
    "greedy": greedy_allocate,
    "optimal": optimal_allocate,
}

HEADER = (
    f"  {'category':<10}{'served':>7}{'unserved':>9}"
    f"{'mean':>8}{'worst':>8}{'gini':>7}"
)


def minutes(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


def show(name: str, allocator: Allocator) -> None:
    result = simulate(SCENARIO, allocator=allocator)
    report = fairness_report(INCIDENT, result)

    print(f"\n{name}  (the run ends at minute {result.end_time:.0f})")
    print(HEADER)
    for row in report.categories:
        print(
            f"  {row.category.name:<10}{row.transported:>7}{row.unserved:>9}"
            f"{minutes(row.mean_wait):>8}{minutes(row.worst_wait):>8}"
            f"{row.gini:>7.2f}"
        )
    for item in sorted(result.transports, key=lambda t: t.casualty_id):
        print(
            f"  {item.casualty_id} -> {item.hospital_id} "
            f"(arrives at hospital: minute {item.delivered_at:.0f})"
        )
    left = ", ".join(result.unserved) if result.unserved else "nobody"
    print(f"  never served: {left}")


def main() -> None:
    print("The same incident, two ways of choosing hospitals.")
    for name, allocator in ALLOCATORS.items():
        show(name, allocator)


if __name__ == "__main__":
    main()

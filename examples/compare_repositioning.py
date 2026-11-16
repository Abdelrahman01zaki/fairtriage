"""Compare where ambulances wait after a delivery, on one fixed incident.

Run it from the project root:  python examples/compare_repositioning.py
"""

from ai_intelligence_lab.environments.road_network import Junction, Road, RoadNetwork
from ai_intelligence_lab.fairtriage.domain.ambulance import Ambulance
from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.domain.hospital import Hospital
from ai_intelligence_lab.fairtriage.domain.incident import Incident
from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.fairness.metrics import fairness_report
from ai_intelligence_lab.fairtriage.simulation.engine import simulate
from ai_intelligence_lab.fairtriage.simulation.repositioning import POLICIES
from ai_intelligence_lab.fairtriage.simulation.scenario import Scenario

RED = TriageCategory.RED
YELLOW = TriageCategory.YELLOW
GREEN = TriageCategory.GREEN
BLACK = TriageCategory.BLACK

NETWORK = RoadNetwork(
    (
        Junction("BASE", 0.0, 0.0),
        Junction("SCENE", 10.0, 0.0),
        Junction("H1", 14.0, 0.0),
        Junction("H2", 10.0, -8.0),
    ),
    (
        Road("BASE", "SCENE", 10.0),
        Road("SCENE", "H1", 4.0),
        Road("SCENE", "H2", 8.0),
    ),
)

INCIDENT = Incident(
    "DEMO",
    "SCENE",
    (
        Casualty("R1", RED, 0.0),
        Casualty("R2", RED, 0.0),
        Casualty("Y1", YELLOW, 0.0),
        Casualty("Y2", YELLOW, 2.0),
        Casualty("Y3", YELLOW, 5.0),
        Casualty("G1", GREEN, 0.0),
        Casualty("G2", GREEN, 6.0),
        Casualty("B1", BLACK, 3.0),
    ),
)

SCENARIO = Scenario(
    NETWORK,
    INCIDENT,
    (Hospital("H1", "H1", 4), Hospital("H2", "H2", 6)),
    (Ambulance("A1", "BASE"), Ambulance("A2", "BASE")),
)

HEADER = (
    f"  {'category':<10}{'served':>7}{'unserved':>9}"
    f"{'mean':>8}{'worst':>8}{'gini':>7}"
)


def minutes(value: float | None) -> str:
    return "-" if value is None else f"{value:.1f}"


def show(name: str) -> None:
    result = simulate(SCENARIO, repositioning=POLICIES[name])
    report = fairness_report(INCIDENT, result)

    print(f"\n{name}  (the run ends at minute {result.end_time:.0f})")
    print(HEADER)
    for row in report.categories:
        print(
            f"  {row.category.name:<10}{row.transported:>7}{row.unserved:>9}"
            f"{minutes(row.mean_wait):>8}{minutes(row.worst_wait):>8}"
            f"{row.gini:>7.2f}"
        )


def main() -> None:
    print("Minutes a casualty waited for an ambulance, by START category.")
    for name in POLICIES:
        show(name)


if __name__ == "__main__":
    main()

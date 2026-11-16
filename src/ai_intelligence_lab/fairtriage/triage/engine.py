"""Triage engine: from a rescuer's observations to a casualty ready to simulate.

``triage_casualty`` is the one entry point. It keeps the deciding rule next to
the casualty, so any category can be explained after the fact.
"""

from dataclasses import dataclass

from ai_intelligence_lab.fairtriage.domain.casualty import Casualty
from ai_intelligence_lab.fairtriage.triage.assessment import Assessment
from ai_intelligence_lab.fairtriage.triage.start import TriageDecision, classify


@dataclass(frozen=True, slots=True)
class TriageResult:
    """A triaged casualty together with the decision that produced its category."""

    casualty: Casualty
    decision: TriageDecision

    def __post_init__(self) -> None:
        if self.casualty.category is not self.decision.category:
            raise ValueError(
                f"casualty {self.casualty.id!r} has category "
                f"{self.casualty.category.name} but the decision says "
                f"{self.decision.category.name}"
            )

    def explain(self) -> str:
        """One plain sentence saying which category was given and why."""
        return (
            f"{self.casualty.id}: {self.casualty.category.name} "
            f"because {self.decision.rule.value}"
        )


def triage_casualty(
    casualty_id: str, reported_at: float, assessment: Assessment
) -> TriageResult:
    """Classify ``assessment`` and build the casualty with the decided category."""
    decision = classify(assessment)
    casualty = Casualty(casualty_id, decision.category, reported_at)
    return TriageResult(casualty, decision)

"""START decision rules: from observations to a triage category.

The rules are checked in a fixed order and the first one that applies decides.
The result names that rule, so every decision can be explained in plain words.

This is a teaching model of the generally published START steps for adults.
It is not a medical protocol and must not be used on real patients.
"""

from dataclasses import dataclass
from enum import Enum

from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory
from ai_intelligence_lab.fairtriage.triage.assessment import Assessment

MAX_BREATHS_PER_MINUTE = 30.0
MAX_CAPILLARY_REFILL_SECONDS = 2.0


class StartRule(Enum):
    """The rule that decided a category, in words a person can read."""

    CAN_WALK = "can walk"
    NOT_BREATHING = "not breathing even after the airway was opened"
    BREATHES_AFTER_AIRWAY = "breathes only after the airway was opened"
    BREATHING_TOO_FAST = "breathing more than 30 times a minute"
    POOR_CIRCULATION = "no radial pulse or capillary refill over 2 seconds"
    CANNOT_FOLLOW_COMMANDS = "cannot follow simple commands"
    OTHERWISE = "none of the urgent signs found"


@dataclass(frozen=True, slots=True)
class TriageDecision:
    category: TriageCategory
    rule: StartRule


def classify(assessment: Assessment) -> TriageDecision:
    """Apply the START steps in order and return the category with its rule."""
    if assessment.can_walk:
        return TriageDecision(TriageCategory.GREEN, StartRule.CAN_WALK)

    if assessment.breaths_per_minute == 0:
        if assessment.breathes_after_airway_opened:
            return TriageDecision(TriageCategory.RED, StartRule.BREATHES_AFTER_AIRWAY)
        return TriageDecision(TriageCategory.BLACK, StartRule.NOT_BREATHING)

    if assessment.breaths_per_minute > MAX_BREATHS_PER_MINUTE:
        return TriageDecision(TriageCategory.RED, StartRule.BREATHING_TOO_FAST)

    if (
        not assessment.radial_pulse_present
        or assessment.capillary_refill_seconds > MAX_CAPILLARY_REFILL_SECONDS
    ):
        return TriageDecision(TriageCategory.RED, StartRule.POOR_CIRCULATION)

    if not assessment.obeys_commands:
        return TriageDecision(TriageCategory.RED, StartRule.CANNOT_FOLLOW_COMMANDS)

    return TriageDecision(TriageCategory.YELLOW, StartRule.OTHERWISE)

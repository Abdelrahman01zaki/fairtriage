"""Triage categories used by the START system.

This module describes the medical assessment of a casualty and nothing else.
How scarce resources are shared out is decided elsewhere, so that fairness can
be measured separately from the medical judgement.
"""

from enum import Enum


class TriageCategory(Enum):
    """The four START categories, named by their tag colour."""

    RED = "immediate"
    YELLOW = "delayed"
    GREEN = "minor"
    BLACK = "expectant"

    @property
    def urgency(self) -> int:
        """Treatment order: 0 is the most urgent, larger numbers can wait."""
        return _TREATMENT_ORDER.index(self)


_TREATMENT_ORDER = (
    TriageCategory.RED,
    TriageCategory.YELLOW,
    TriageCategory.GREEN,
    TriageCategory.BLACK,
)

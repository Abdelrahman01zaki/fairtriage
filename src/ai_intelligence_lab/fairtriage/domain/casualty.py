"""A casualty: one person who has been triaged and is waiting for care.

Times are minutes since the incident began. The casualty knows how long it
has waited, because waiting time is what the fairness measures are built on.

``needs`` names the specialties the casualty must be treated in, in the same
words as ``Hospital.specialties``. It is empty when no special care is needed.
"""

import math
from dataclasses import dataclass

from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory


@dataclass(frozen=True, slots=True)
class Casualty:
    id: str
    category: TriageCategory
    reported_at: float
    needs: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("a casualty needs an id")
        if not isinstance(self.category, TriageCategory):
            raise ValueError(f"casualty {self.id!r}: category must be a TriageCategory")
        if not math.isfinite(self.reported_at) or self.reported_at < 0:
            raise ValueError(
                f"casualty {self.id!r}: reported_at must be a finite time "
                "of zero or more minutes"
            )
        if isinstance(self.needs, str):
            raise ValueError(f"casualty {self.id!r}: needs must be a collection")
        object.__setattr__(self, "needs", frozenset(self.needs))

    def waited(self, now: float) -> float:
        """Minutes this casualty has been waiting at time ``now``."""
        if not math.isfinite(now) or now < self.reported_at:
            raise ValueError(
                f"casualty {self.id!r}: time {now} is before it was reported"
            )
        return now - self.reported_at

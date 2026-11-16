"""What a rescuer observes about one casualty, as the START steps ask for it.

This is only the observations. Turning them into a triage category is done
elsewhere, so the inputs and the decision rules can be tested separately.
"""

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Assessment:
    """One set of observations.

    ``breaths_per_minute`` of 0 means the casualty is not breathing.
    ``breathes_after_airway_opened`` only applies to a casualty who is not
    breathing at first, so it must stay False when the rate is above 0.
    """

    can_walk: bool
    breaths_per_minute: float
    radial_pulse_present: bool
    capillary_refill_seconds: float
    obeys_commands: bool
    breathes_after_airway_opened: bool = False

    def __post_init__(self) -> None:
        _require_zero_or_more("breaths_per_minute", self.breaths_per_minute)
        _require_zero_or_more("capillary_refill_seconds", self.capillary_refill_seconds)
        if self.breaths_per_minute > 0 and self.breathes_after_airway_opened:
            raise ValueError(
                "breathes_after_airway_opened only applies to a casualty "
                "who is not breathing"
            )


def _require_zero_or_more(name: str, value: float) -> None:
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite number of zero or more")

"""A queue of things that will happen, handed out in the order of their time.

The queue knows nothing about ambulances or casualties. It holds any payload
together with the time it happens. Two events at the same time come out in the
order they were scheduled, so a run is repeatable.

``now`` is the time of the last event handed out. Nothing can be scheduled
before it, because the past cannot change.
"""

import heapq
import itertools
import math
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Scheduled(Generic[T]):
    """A payload and the time at which it happens."""

    time: float
    payload: T


class EventQueue(Generic[T]):
    def __init__(self) -> None:
        # The counter breaks ties, so payloads are never compared.
        self._heap: list[tuple[float, int, T]] = []
        self._order = itertools.count()
        self._now = 0.0

    @property
    def now(self) -> float:
        return self._now

    def __len__(self) -> int:
        return len(self._heap)

    def schedule(self, time: float, payload: T) -> None:
        if not math.isfinite(time) or time < self._now:
            raise ValueError(
                f"cannot schedule at {time}: it must be a finite time "
                f"of {self._now} or later"
            )
        heapq.heappush(self._heap, (time, next(self._order), payload))

    def peek_time(self) -> float | None:
        """The time of the next event, or None when the queue is empty."""
        return self._heap[0][0] if self._heap else None

    def pop(self) -> Scheduled[T]:
        """Take the next event and move ``now`` to its time."""
        if not self._heap:
            raise IndexError("no events are left")
        time, _, payload = heapq.heappop(self._heap)
        self._now = time
        return Scheduled(time, payload)

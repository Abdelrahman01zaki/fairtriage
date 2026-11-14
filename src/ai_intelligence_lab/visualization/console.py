"""Console consumer: prints algorithm events as text, one line per event.

This lives in `visualization/` because formatting is presentation. The
algorithms know nothing about it; they only produce AlgorithmEvent objects.
"""

import sys
from collections.abc import Iterable
from typing import TextIO

from ai_intelligence_lab.core.events import AlgorithmEvent


def format_event(step: int, event: AlgorithmEvent) -> str:
    """Turn one event into one line of text. Missing fields are skipped."""
    parts = [f"{step:>3}", f"{event.kind.name:<15}"]
    if event.node is not None:
        parts.append(f"node={event.node}")
    if event.parent is not None:
        parts.append(f"parent={event.parent}")
    if event.cost is not None:
        parts.append(f"cost={event.cost:g}")
    if event.path is not None:
        parts.append("path=" + " -> ".join(str(cell) for cell in event.path))
    return "  ".join(parts).rstrip()


def print_events(events: Iterable[AlgorithmEvent], out: TextIO | None = None) -> int:
    """Print every event as it arrives and return how many were printed."""
    if out is None:
        out = sys.stdout  # resolved at call time so tests can capture it
    count = 0
    for step, event in enumerate(events, start=1):
        print(format_event(step, event), file=out)
        count = step
    return count

"""Heuristic functions shared by the informed search algorithms."""

from ai_intelligence_lab.environments.grid import Position


def manhattan(a: Position, b: Position) -> int:
    """Grid distance if you could only move up, down, left or right."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

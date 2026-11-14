"""Rectangular grid world used by the search algorithms."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType

Position = tuple[int, int]  # (row, column)

# Fixed order: up, right, down, left. A fixed order keeps every run
# deterministic, so the same grid always produces the same events.
_DIRECTIONS: tuple[Position, ...] = ((-1, 0), (0, 1), (1, 0), (0, -1))

DEFAULT_COST = 1.0


@dataclass(frozen=True, slots=True)
class Grid:
    """An immutable grid with walls, one start cell, one goal cell, and
    an optional per-cell movement cost.

    ``weights`` maps a cell to the cost of *entering* it. A cell with no
    entry costs ``DEFAULT_COST`` (1.0), so BFS and DFS - which never look
    at weights - behave exactly as before: every step still costs 1.
    """

    height: int
    width: int
    start: Position
    goal: Position
    walls: frozenset[Position] = frozenset()
    weights: Mapping[Position, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Type hints are not enforced at runtime: a caller may pass a plain
        # set or dict. Freeze private copies so the grid is truly immutable.
        object.__setattr__(self, "walls", frozenset(self.walls))
        object.__setattr__(self, "weights", MappingProxyType(dict(self.weights)))

        if self.height <= 0 or self.width <= 0:
            raise ValueError("grid size must be positive")
        for name, cell in (("start", self.start), ("goal", self.goal)):
            if not self.in_bounds(cell):
                raise ValueError(f"{name} {cell} is outside the grid")
            if cell in self.walls:
                raise ValueError(f"{name} {cell} is on a wall")
        for wall in self.walls:
            if not self.in_bounds(wall):
                raise ValueError(f"wall {wall} is outside the grid")
        for cell, weight in self.weights.items():
            if not self.in_bounds(cell):
                raise ValueError(f"weighted cell {cell} is outside the grid")
            if cell in self.walls:
                raise ValueError(f"weighted cell {cell} is a wall")
            if not math.isfinite(weight) or weight <= 0:
                raise ValueError(f"weight for {cell} must be positive and finite")

    def in_bounds(self, cell: Position) -> bool:
        row, col = cell
        return 0 <= row < self.height and 0 <= col < self.width

    def is_walkable(self, cell: Position) -> bool:
        return self.in_bounds(cell) and cell not in self.walls

    def neighbors(self, cell: Position) -> tuple[Position, ...]:
        row, col = cell
        candidates = ((row + dr, col + dc) for dr, dc in _DIRECTIONS)
        return tuple(c for c in candidates if self.is_walkable(c))

    def cost(self, cell: Position) -> float:
        """Cost of entering ``cell``. Unweighted cells cost DEFAULT_COST."""
        return self.weights.get(cell, DEFAULT_COST)

    @classmethod
    def from_text(
        cls,
        rows: Sequence[str],
        weights: Mapping[Position, float] | None = None,
    ) -> "Grid":
        """Build a grid from text: '#' wall, '.' free, 'S' start, 'G' goal."""
        if not rows:
            raise ValueError("grid needs at least one row")
        width = len(rows[0])
        walls: set[Position] = set()
        start: Position | None = None
        goal: Position | None = None

        for r, line in enumerate(rows):
            if len(line) != width:
                raise ValueError("all rows must have the same length")
            for c, char in enumerate(line):
                if char == "#":
                    walls.add((r, c))
                elif char == "S":
                    if start is not None:
                        raise ValueError("grid has more than one 'S'")
                    start = (r, c)
                elif char == "G":
                    if goal is not None:
                        raise ValueError("grid has more than one 'G'")
                    goal = (r, c)
                elif char != ".":
                    raise ValueError(f"unknown character {char!r}")

        if start is None or goal is None:
            raise ValueError("grid needs one 'S' and one 'G'")
        return cls(len(rows), width, start, goal, frozenset(walls), weights or {})

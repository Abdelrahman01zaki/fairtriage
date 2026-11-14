"""Reproducible grid generators for tests and benchmarks.

Every generator takes a ``seed``. The same arguments and the same seed
always give the same grid, so a benchmark can be repeated exactly.
"""

import random
from collections import deque

from ai_intelligence_lab.environments.grid import Grid, Position

_STEPS: tuple[Position, ...] = ((-1, 0), (0, 1), (1, 0), (0, -1))


def _is_solvable(
    height: int,
    width: int,
    walls: set[Position],
    start: Position,
    goal: Position,
) -> bool:
    """Flood fill, independent of the algorithms under test."""
    seen = {start}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        if cell == goal:
            return True
        for dr, dc in _STEPS:
            nxt = (cell[0] + dr, cell[1] + dc)
            if (
                0 <= nxt[0] < height
                and 0 <= nxt[1] < width
                and nxt not in walls
                and nxt not in seen
            ):
                seen.add(nxt)
                queue.append(nxt)
    return False


def random_grid(
    height: int,
    width: int,
    *,
    wall_density: float = 0.25,
    max_weight: int | None = None,
    seed: int = 0,
    max_attempts: int = 1000,
) -> Grid:
    """A grid with random walls. Start is top-left, goal is bottom-right.

    The result is always solvable: unsolvable draws are thrown away and
    drawn again. With ``max_weight`` set, about 30% of the open cells get
    an integer weight between 2 and ``max_weight``.
    """
    if height * width < 2:
        raise ValueError("grid needs at least two cells")
    if not 0.0 <= wall_density < 1.0:
        raise ValueError("wall_density must be in [0, 1)")
    if max_weight is not None and max_weight < 2:
        raise ValueError("max_weight must be at least 2")

    rng = random.Random(seed)
    start: Position = (0, 0)
    goal: Position = (height - 1, width - 1)
    cells = [(r, c) for r in range(height) for c in range(width)]

    for _ in range(max_attempts):
        walls = {
            cell
            for cell in cells
            if cell not in (start, goal) and rng.random() < wall_density
        }
        if not _is_solvable(height, width, walls, start, goal):
            continue

        weights: dict[Position, float] = {}
        if max_weight is not None:
            for cell in cells:
                if cell not in walls and rng.random() < 0.3:
                    weights[cell] = float(rng.randint(2, max_weight))
        return Grid(height, width, start, goal, frozenset(walls), weights)

    raise ValueError(
        f"could not generate a solvable grid after {max_attempts} attempts"
    )


def maze(height: int, width: int, *, seed: int = 0) -> Grid:
    """A perfect maze: exactly one route between any two open cells.

    Built with a randomized depth-first carve. Both sizes must be odd, so
    that start (top-left) and goal (bottom-right) are both rooms.
    """
    if height < 3 or width < 3 or height % 2 == 0 or width % 2 == 0:
        raise ValueError("maze size must be odd and at least 3x3")

    rng = random.Random(seed)
    open_cells: set[Position] = {(0, 0)}
    stack: list[Position] = [(0, 0)]

    while stack:
        row, col = stack[-1]
        candidates = [
            (row + dr, col + dc)
            for dr, dc in ((-2, 0), (0, 2), (2, 0), (0, -2))
            if 0 <= row + dr < height
            and 0 <= col + dc < width
            and (row + dr, col + dc) not in open_cells
        ]
        if not candidates:
            stack.pop()
            continue

        nxt = rng.choice(candidates)
        between = ((row + nxt[0]) // 2, (col + nxt[1]) // 2)
        open_cells.update((between, nxt))
        stack.append(nxt)

    walls = frozenset(
        (r, c) for r in range(height) for c in range(width) if (r, c) not in open_cells
    )
    return Grid(height, width, (0, 0), (height - 1, width - 1), walls)

"""Run BFS on a small grid and print every event."""

from ai_intelligence_lab.algorithms.search.bfs import bfs
from ai_intelligence_lab.environments.grid import Grid
from ai_intelligence_lab.visualization.console import print_events

grid = Grid.from_text(
    [
        "S.#.",
        "..#.",
        "...G",
    ]
)

total = print_events(bfs(grid))
print(f"\n{total} events")

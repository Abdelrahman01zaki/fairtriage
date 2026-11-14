"""Run BFS, DFS and UCS on a weighted grid and compare their paths."""

from ai_intelligence_lab.algorithms.search.bfs import bfs
from ai_intelligence_lab.algorithms.search.dfs import dfs
from ai_intelligence_lab.algorithms.search.ucs import ucs
from ai_intelligence_lab.environments.grid import Grid
from ai_intelligence_lab.visualization.console import print_events

# (0, 1) is expensive to enter, so the shortest *path* (fewest cells)
# is not the cheapest *route* once movement has a cost.
grid = Grid.from_text(["S.G", "..."], weights={(0, 1): 10.0})

for name, algorithm in (("BFS", bfs), ("DFS", dfs), ("UCS", ucs)):
    print(f"--- {name} ---")
    total = print_events(algorithm(grid))
    print(f"{total} events\n")

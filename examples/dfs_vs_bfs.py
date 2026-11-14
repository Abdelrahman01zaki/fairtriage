"""Run BFS and DFS on the same grid and print every event."""

from ai_intelligence_lab.algorithms.search.bfs import bfs
from ai_intelligence_lab.algorithms.search.dfs import dfs
from ai_intelligence_lab.environments.grid import Grid
from ai_intelligence_lab.visualization.console import print_events

grid = Grid.from_text(["S..", "G.."])

for name, algorithm in (("BFS", bfs), ("DFS", dfs)):
    print(f"--- {name} ---")
    total = print_events(algorithm(grid))
    print(f"{total} events\n")

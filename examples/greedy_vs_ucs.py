"""Compare Greedy best-first search with UCS on a weighted grid."""

from ai_intelligence_lab.algorithms.search.greedy import greedy
from ai_intelligence_lab.algorithms.search.ucs import ucs
from ai_intelligence_lab.environments.grid import Grid
from ai_intelligence_lab.visualization.console import print_events

# Greedy chases the goal and walks through the expensive cell (0, 1);
# UCS pays attention to cost and goes around it.
grid = Grid.from_text(["S.G", "..."], weights={(0, 1): 10.0})

for name, algorithm in (("GREEDY", greedy), ("UCS", ucs)):
    print(f"--- {name} ---")
    total = print_events(algorithm(grid))
    print(f"{total} events\n")

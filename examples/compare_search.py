"""Compare UCS, Greedy and A* on two grids: expanded cells and path cost."""

from ai_intelligence_lab.algorithms.search.astar import astar
from ai_intelligence_lab.algorithms.search.greedy import greedy
from ai_intelligence_lab.algorithms.search.ucs import ucs
from ai_intelligence_lab.core.events import EventType
from ai_intelligence_lab.environments.grid import Grid


def summarize(algorithm, grid):
    expanded = 0
    cost = None
    for event in algorithm(grid):
        if event.kind is EventType.NODE_EXPANDED:
            expanded += 1
        elif event.kind is EventType.PATH_FOUND:
            cost = event.cost
    return expanded, cost


grids = {
    "Open grid 5x5 (all steps cost 1)": Grid.from_text(
        [".....", ".....", "S.G..", ".....", "....."]
    ),
    "Weighted grid ((0, 1) costs 10)": Grid.from_text(
        ["S.G", "..."], weights={(0, 1): 10.0}
    ),
}

for title, grid in grids.items():
    print(title)
    for name, algorithm in (("UCS", ucs), ("Greedy", greedy), ("A*", astar)):
        expanded, cost = summarize(algorithm, grid)
        print(f"  {name:<7} expanded={expanded:<3} path cost={cost:g}")
    print()

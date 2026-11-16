"""The small interface a search algorithm needs from its world.

A grid is one such world. A road network is another. Nodes can be any
hashable value, and the cost belongs to the move from one node to the next,
because on a road the cost depends on which road is taken.
"""

from collections.abc import Hashable, Iterable
from typing import Protocol, TypeVar

Node = TypeVar("Node", bound=Hashable)


class SearchSpace(Protocol[Node]):
    @property
    def start(self) -> Node: ...

    @property
    def goal(self) -> Node: ...

    def neighbors(self, node: Node, /) -> Iterable[Node]: ...

    def step_cost(self, source: Node, target: Node, /) -> float: ...

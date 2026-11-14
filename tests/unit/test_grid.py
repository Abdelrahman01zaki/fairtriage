import dataclasses

import pytest

from ai_intelligence_lab.environments.grid import Grid


def test_from_text_parses_layout():
    grid = Grid.from_text(["S#.", "...", "..G"])

    assert grid.height == 3
    assert grid.width == 3
    assert grid.start == (0, 0)
    assert grid.goal == (2, 2)
    assert grid.walls == frozenset({(0, 1)})


def test_neighbors_in_open_space_follow_fixed_order():
    grid = Grid.from_text(["S..", "...", "..G"])

    # up, right, down, left
    assert grid.neighbors((1, 1)) == ((0, 1), (1, 2), (2, 1), (1, 0))


def test_neighbors_skip_out_of_bounds_cells():
    grid = Grid.from_text(["S..", "...", "..G"])

    assert grid.neighbors((0, 0)) == ((0, 1), (1, 0))


def test_neighbors_skip_walls():
    grid = Grid.from_text(["S#.", "...", "..G"])

    assert grid.neighbors((0, 0)) == ((1, 0),)


def test_is_walkable():
    grid = Grid.from_text(["S#.", "...", "..G"])

    assert grid.is_walkable((0, 2))
    assert not grid.is_walkable((0, 1))  # wall
    assert not grid.is_walkable((3, 0))  # outside


@pytest.mark.parametrize(
    "rows",
    [
        [],                      # no rows
        ["S..", "..."],          # no goal
        ["...", "..G"],          # no start
        ["S.S", "..G"],          # two starts
        ["S..", "..", "..G"],    # rows of different length
        ["S.x", "..G"],          # unknown character
    ],
)
def test_from_text_rejects_invalid_layouts(rows):
    with pytest.raises(ValueError):
        Grid.from_text(rows)


def test_start_on_wall_is_rejected():
    with pytest.raises(ValueError):
        Grid(2, 2, start=(0, 0), goal=(1, 1), walls=frozenset({(0, 0)}))


def test_goal_outside_grid_is_rejected():
    with pytest.raises(ValueError):
        Grid(2, 2, start=(0, 0), goal=(5, 5))


def test_wall_outside_grid_is_rejected():
    with pytest.raises(ValueError):
        Grid(2, 2, start=(0, 0), goal=(1, 1), walls=frozenset({(9, 9)}))


def test_grid_is_immutable():
    grid = Grid.from_text(["S.G"])

    with pytest.raises(dataclasses.FrozenInstanceError):
        grid.width = 10

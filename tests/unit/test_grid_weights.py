import pytest

from ai_intelligence_lab.environments.grid import DEFAULT_COST, Grid


def test_unweighted_cell_costs_default():
    grid = Grid.from_text(["S.G"])
    assert grid.cost((0, 1)) == DEFAULT_COST


def test_weighted_cell_costs_its_weight():
    grid = Grid.from_text(["S.G"], weights={(0, 1): 5.0})
    assert grid.cost((0, 1)) == 5.0


def test_cells_not_in_weights_still_cost_default():
    grid = Grid.from_text(["S..G"], weights={(0, 1): 3.0})
    assert grid.cost((0, 2)) == DEFAULT_COST


def test_weight_on_a_wall_is_rejected():
    with pytest.raises(ValueError, match="wall"):
        Grid.from_text(["S#G"], weights={(0, 1): 5.0})


def test_weight_outside_grid_is_rejected():
    with pytest.raises(ValueError, match="outside the grid"):
        Grid(1, 3, start=(0, 0), goal=(0, 2), weights={(5, 5): 2.0})


def test_zero_or_negative_weight_is_rejected():
    with pytest.raises(ValueError, match="positive"):
        Grid.from_text(["S.G"], weights={(0, 1): 0.0})

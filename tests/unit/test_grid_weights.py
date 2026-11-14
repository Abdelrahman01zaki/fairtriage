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


@pytest.mark.parametrize("bad", [-1.0, float("nan"), float("inf")])
def test_negative_nan_or_infinite_weight_is_rejected(bad):
    with pytest.raises(ValueError, match="positive and finite"):
        Grid.from_text(["S.G"], weights={(0, 1): bad})


def test_weights_cannot_be_changed_through_the_grid():
    grid = Grid.from_text(["S.G"], weights={(0, 1): 5.0})

    with pytest.raises(TypeError):
        grid.weights[(0, 1)] = 1.0


def test_changing_the_source_dict_does_not_change_the_grid():
    source = {(0, 1): 5.0}
    grid = Grid.from_text(["S.G"], weights=source)

    source[(0, 1)] = 1.0

    assert grid.cost((0, 1)) == 5.0

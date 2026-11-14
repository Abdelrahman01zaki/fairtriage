from ai_intelligence_lab.environments.grid import Grid


def test_single_cell_path_costs_nothing():
    grid = Grid.from_text(["S.G"])

    assert grid.path_cost(((0, 0),)) == 0.0


def test_unweighted_path_costs_one_per_step():
    grid = Grid.from_text(["S.G"])

    assert grid.path_cost(((0, 0), (0, 1), (0, 2))) == 2.0


def test_weighted_cells_add_their_own_cost():
    grid = Grid.from_text(["S.G"], weights={(0, 1): 5.0})

    assert grid.path_cost(((0, 0), (0, 1), (0, 2))) == 6.0


def test_start_cell_weight_is_never_paid():
    grid = Grid.from_text(["S.G"], weights={(0, 0): 9.0})

    assert grid.path_cost(((0, 0), (0, 1), (0, 2))) == 2.0

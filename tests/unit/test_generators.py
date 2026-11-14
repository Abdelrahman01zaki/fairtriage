import pytest

from ai_intelligence_lab.algorithms.search.bfs import bfs
from ai_intelligence_lab.algorithms.search.dfs import dfs
from ai_intelligence_lab.environments.generators import maze, random_grid
from ai_intelligence_lab.evaluation.metrics import measure


def _same(a, b):
    return (
        (a.height, a.width, a.start, a.goal) == (b.height, b.width, b.start, b.goal)
        and a.walls == b.walls
        and dict(a.weights) == dict(b.weights)
    )


def test_random_grid_same_seed_gives_same_grid():
    a = random_grid(12, 12, wall_density=0.3, max_weight=5, seed=7)
    b = random_grid(12, 12, wall_density=0.3, max_weight=5, seed=7)

    assert _same(a, b)


def test_random_grid_different_seeds_give_different_grids():
    a = random_grid(12, 12, wall_density=0.3, seed=1)
    b = random_grid(12, 12, wall_density=0.3, seed=2)

    assert a.walls != b.walls


def test_random_grid_is_always_solvable():
    for seed in range(20):
        grid = random_grid(15, 15, wall_density=0.3, seed=seed)

        assert measure(grid, bfs(grid)).found


def test_random_grid_size_and_corners():
    grid = random_grid(6, 9, seed=3)

    assert (grid.height, grid.width) == (6, 9)
    assert grid.start == (0, 0)
    assert grid.goal == (5, 8)


def test_zero_density_has_no_walls():
    assert random_grid(5, 5, wall_density=0.0).walls == frozenset()


@pytest.mark.parametrize("bad", [1.0, -0.1])
def test_wall_density_out_of_range_is_rejected(bad):
    with pytest.raises(ValueError, match="wall_density"):
        random_grid(5, 5, wall_density=bad)


def test_hopeless_density_raises_instead_of_looping_forever():
    with pytest.raises(ValueError, match="solvable"):
        random_grid(10, 10, wall_density=0.99, max_attempts=5, seed=0)


def test_weights_stay_in_range():
    grid = random_grid(10, 10, wall_density=0.2, max_weight=5, seed=4)

    assert len(grid.weights) > 0
    assert all(2.0 <= w <= 5.0 for w in grid.weights.values())


def test_no_weights_by_default():
    assert len(random_grid(5, 5, seed=1).weights) == 0


def test_max_weight_below_two_is_rejected():
    with pytest.raises(ValueError, match="max_weight"):
        random_grid(5, 5, max_weight=1)


def test_maze_is_a_perfect_maze():
    # A spanning tree over R rooms has R - 1 corridors between them:
    # R rooms + (R - 1) corridor cells = 2R - 1 open cells.
    grid = maze(11, 15, seed=3)
    rooms = ((11 + 1) // 2) * ((15 + 1) // 2)

    assert 11 * 15 - len(grid.walls) == 2 * rooms - 1


def test_maze_has_a_single_route_so_bfs_and_dfs_agree():
    grid = maze(15, 15, seed=5)

    bfs_path = measure(grid, bfs(grid)).path
    dfs_path = measure(grid, dfs(grid)).path

    assert bfs_path is not None
    assert bfs_path == dfs_path


def test_maze_same_seed_gives_same_maze():
    assert _same(maze(9, 9, seed=2), maze(9, 9, seed=2))


@pytest.mark.parametrize("size", [(4, 5), (5, 4), (1, 5)])
def test_maze_rejects_even_or_tiny_sizes(size):
    with pytest.raises(ValueError, match="odd"):
        maze(*size)

from ai_intelligence_lab.algorithms.search.paths import build_path


def test_path_of_single_cell():
    assert build_path({(0, 0): None}, (0, 0)) == ((0, 0),)


def test_path_follows_parent_links_back_to_start():
    parents = {(0, 0): None, (0, 1): (0, 0), (0, 2): (0, 1)}

    assert build_path(parents, (0, 2)) == ((0, 0), (0, 1), (0, 2))


def test_path_ignores_unrelated_entries():
    parents = {(0, 0): None, (0, 1): (0, 0), (5, 5): (0, 0)}

    assert build_path(parents, (0, 1)) == ((0, 0), (0, 1))

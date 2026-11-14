from ai_intelligence_lab.algorithms.search.heuristics import manhattan


def test_manhattan_is_sum_of_row_and_column_gaps():
    assert manhattan((0, 0), (2, 3)) == 5


def test_manhattan_is_symmetric():
    assert manhattan((4, 1), (0, 5)) == manhattan((0, 5), (4, 1))


def test_manhattan_to_itself_is_zero():
    assert manhattan((2, 2), (2, 2)) == 0

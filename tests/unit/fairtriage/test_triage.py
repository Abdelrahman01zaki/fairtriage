from ai_intelligence_lab.fairtriage.domain.triage import TriageCategory

RED = TriageCategory.RED
YELLOW = TriageCategory.YELLOW
GREEN = TriageCategory.GREEN
BLACK = TriageCategory.BLACK


def test_there_are_exactly_four_categories():
    assert [c.name for c in TriageCategory] == ["RED", "YELLOW", "GREEN", "BLACK"]


def test_each_category_has_a_plain_meaning():
    assert RED.value == "immediate"
    assert YELLOW.value == "delayed"
    assert GREEN.value == "minor"
    assert BLACK.value == "expectant"


def test_urgency_runs_from_red_to_black():
    assert [c.urgency for c in (RED, YELLOW, GREEN, BLACK)] == [0, 1, 2, 3]


def test_every_category_has_its_own_urgency():
    urgencies = [c.urgency for c in TriageCategory]

    assert len(set(urgencies)) == len(urgencies)


def test_sorting_by_urgency_puts_the_most_urgent_first():
    shuffled = [GREEN, BLACK, RED, YELLOW]

    assert sorted(shuffled, key=lambda c: c.urgency) == [RED, YELLOW, GREEN, BLACK]


def test_red_is_more_urgent_than_yellow():
    assert RED.urgency < YELLOW.urgency

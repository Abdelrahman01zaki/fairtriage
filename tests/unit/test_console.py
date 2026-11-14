import io
from itertools import islice

from ai_intelligence_lab.algorithms.search.bfs import bfs
from ai_intelligence_lab.core.events import AlgorithmEvent, EventType
from ai_intelligence_lab.environments.grid import Grid
from ai_intelligence_lab.visualization.console import format_event, print_events


def test_format_shows_step_kind_and_node():
    line = format_event(1, AlgorithmEvent(EventType.STARTED, node=(0, 0)))

    assert line.split()[0] == "1"
    assert "STARTED" in line
    assert "node=(0, 0)" in line


def test_format_skips_missing_fields():
    line = format_event(2, AlgorithmEvent(EventType.COMPLETED))

    assert "node" not in line
    assert "parent" not in line
    assert "path" not in line


def test_format_shows_parent():
    event = AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 1), parent=(0, 0))

    assert "parent=(0, 0)" in format_event(3, event)


def test_format_shows_path_with_arrows():
    event = AlgorithmEvent(EventType.PATH_FOUND, node=(0, 1), path=((0, 0), (0, 1)))

    assert "path=(0, 0) -> (0, 1)" in format_event(4, event)


def test_format_has_no_trailing_spaces():
    line = format_event(5, AlgorithmEvent(EventType.COMPLETED))

    assert line == line.rstrip()


def test_print_events_numbers_steps_and_returns_count():
    out = io.StringIO()

    count = print_events(bfs(Grid.from_text(["S.G"])), out)

    lines = out.getvalue().splitlines()
    assert count == 8
    assert len(lines) == 8
    assert lines[0].split()[0] == "1"
    assert lines[-1].split()[0] == "8"
    assert "COMPLETED" in lines[-1]


def test_print_events_uses_stdout_by_default(capsys):
    print_events([AlgorithmEvent(EventType.STARTED, node=(0, 0))])

    assert "STARTED" in capsys.readouterr().out


def test_print_events_can_consume_only_part_of_a_run():
    out = io.StringIO()
    first_three = islice(bfs(Grid.from_text(["S.G"])), 3)

    count = print_events(first_three, out)

    assert count == 3
    assert "PATH_FOUND" not in out.getvalue()


def test_print_events_with_no_events():
    out = io.StringIO()

    assert print_events([], out) == 0
    assert out.getvalue() == ""

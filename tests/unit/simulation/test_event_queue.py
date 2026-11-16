import pytest

from ai_intelligence_lab.simulation.event_queue import EventQueue


def test_events_come_out_in_time_order():
    queue: EventQueue[str] = EventQueue()
    queue.schedule(5.0, "c")
    queue.schedule(1.0, "a")
    queue.schedule(3.0, "b")

    assert [queue.pop().payload for _ in range(3)] == ["a", "b", "c"]


def test_equal_times_keep_the_order_they_were_scheduled():
    queue: EventQueue[str] = EventQueue()
    for name in ("first", "second", "third"):
        queue.schedule(2.0, name)

    assert [queue.pop().payload for _ in range(3)] == ["first", "second", "third"]


def test_payloads_are_never_compared():
    queue: EventQueue[object] = EventQueue()
    queue.schedule(1.0, object())
    queue.schedule(1.0, object())

    queue.pop()
    queue.pop()


def test_now_moves_to_the_time_of_the_event_taken():
    queue: EventQueue[str] = EventQueue()
    queue.schedule(4.0, "x")

    assert queue.now == 0.0
    assert queue.pop().time == 4.0
    assert queue.now == 4.0


def test_the_past_cannot_be_scheduled():
    queue: EventQueue[str] = EventQueue()
    queue.schedule(4.0, "x")
    queue.pop()

    with pytest.raises(ValueError):
        queue.schedule(3.9, "late")


def test_an_event_may_be_scheduled_at_the_current_time():
    queue: EventQueue[str] = EventQueue()
    queue.schedule(4.0, "x")
    queue.pop()
    queue.schedule(4.0, "same moment")

    assert queue.pop().payload == "same moment"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0])
def test_a_bad_time_is_rejected(bad):
    queue: EventQueue[str] = EventQueue()

    with pytest.raises(ValueError):
        queue.schedule(bad, "x")


def test_peek_time_and_length():
    queue: EventQueue[str] = EventQueue()
    assert queue.peek_time() is None
    assert len(queue) == 0

    queue.schedule(2.0, "x")
    queue.schedule(1.0, "y")

    assert queue.peek_time() == 1.0
    assert len(queue) == 2


def test_taking_from_an_empty_queue_fails():
    queue: EventQueue[str] = EventQueue()

    with pytest.raises(IndexError):
        queue.pop()

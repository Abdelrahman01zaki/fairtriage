import dataclasses

import pytest

from ai_intelligence_lab.core.events import AlgorithmEvent, EventType


def test_optional_fields_default_to_none():
    event = AlgorithmEvent(EventType.STARTED)

    assert event.kind is EventType.STARTED
    assert event.node is None
    assert event.parent is None
    assert event.path is None


def test_event_keeps_given_values():
    path = ((0, 0), (1, 0), (1, 1))
    event = AlgorithmEvent(
        EventType.PATH_FOUND, node=(1, 1), parent=(1, 0), path=path
    )

    assert event.node == (1, 1)
    assert event.parent == (1, 0)
    assert event.path == path


def test_event_is_immutable():
    event = AlgorithmEvent(EventType.NODE_DISCOVERED, node=(0, 1))

    with pytest.raises(dataclasses.FrozenInstanceError):
        event.node = (5, 5)


def test_events_with_same_values_are_equal():
    first = AlgorithmEvent(EventType.NODE_EXPANDED, node=(2, 3))
    second = AlgorithmEvent(EventType.NODE_EXPANDED, node=(2, 3))

    assert first == second


def test_events_with_different_kind_are_not_equal():
    discovered = AlgorithmEvent(EventType.NODE_DISCOVERED, node=(2, 3))
    expanded = AlgorithmEvent(EventType.NODE_EXPANDED, node=(2, 3))

    assert discovered != expanded


def test_event_can_be_used_in_a_set():
    first = AlgorithmEvent(EventType.NODE_DISCOVERED, node=(1, 1))
    second = AlgorithmEvent(EventType.NODE_DISCOVERED, node=(1, 1))

    assert len({first, second}) == 1


def test_event_has_no_instance_dict():
    event = AlgorithmEvent(EventType.STARTED)

    assert not hasattr(event, "__dict__")

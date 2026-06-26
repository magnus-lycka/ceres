"""Unit tests for event_handlers.py — registration bootstrap."""

from ceres.character.domain.event_handlers import register_event_handlers
from ceres.character.mechanism.event_base import EventHandlerBase


def test_register_event_handlers_loads_handlers():
    register_event_handlers()
    assert len(EventHandlerBase._registry) > 0


def test_register_event_handlers_idempotent():
    register_event_handlers()
    count_before = len(EventHandlerBase._registry)
    register_event_handlers()
    assert len(EventHandlerBase._registry) == count_before


def test_survive_handler_registered():
    register_event_handlers()
    assert 'survive' in EventHandlerBase._registry

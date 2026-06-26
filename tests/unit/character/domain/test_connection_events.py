"""Tests for connection event mechanics: handler behaviour, pending ordering."""

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.domain.connection import make_connection
from ceres.character.domain.connection_events import (
    ConnectionNameHandler,
    ConnectionsRollHandler,
    PendingConnectionName,
    PendingConnectionsRoll,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import TextEntry
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD, pending_id


def _projection() -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )


def test_connections_roll_handler_inserts_name_pending_before_existing_pendings():
    """add_connection() inserts PendingConnectionName at index 0, so name prompts appear before
    any pending inputs that were already in the queue when the connections roll was resolved."""
    projection = _projection()
    sentinel_event = Event(handler=ConnectionsRollHandler(connection_type=ConnectionKind.RIVAL, count=0))
    sentinel = PendingConnectionsRoll(
        pending_id=pending_id(sentinel_event, 0),
        instruction='sentinel',
        connection_type=ConnectionKind.CONTACT,
        options=[1],
    )
    projection.pending_inputs.append(sentinel)

    Event(handler=ConnectionsRollHandler(connection_type=ConnectionKind.CONTACT, count=2)).apply(projection)

    name_pendings = [p for p in projection.pending_inputs if isinstance(p, PendingConnectionName)]
    assert len(name_pendings) == 2
    sentinel_idx = projection.pending_inputs.index(sentinel)
    for np in name_pendings:
        assert projection.pending_inputs.index(np) < sentinel_idx


def test_connection_name_handler_sets_name_and_note():
    projection = _projection()
    projection.summary.connections.append(make_connection(ConnectionKind.ALLY, term=0, origin='test'))

    Event(handler=ConnectionNameHandler(connection_index=0, name='Agent Vessa', note='Met on Rhylanor')).apply(
        projection
    )

    conn = projection.summary.connections[0]
    assert conn.name == 'Agent Vessa'
    assert conn.note == 'Met on Rhylanor'


def test_pending_connection_name_event_from_form_creates_event():
    pending = PendingConnectionName(
        pending_id='connection_name_0',
        connection_index=0,
        connection_kind=ConnectionKind.ALLY,
        instruction='Name this Ally',
    )

    event = pending.event_from_form({'name': 'Vessa Koh', 'note': 'Old contact'})

    assert isinstance(event.handler, ConnectionNameHandler)
    assert event.handler.name == 'Vessa Koh'
    assert event.handler.note == 'Old contact'
    assert event.handler.connection_index == 0


def test_pending_connection_name_input_specs_returns_text_fields():
    pending = PendingConnectionName(
        pending_id='connection_name_0',
        connection_index=0,
        connection_kind=ConnectionKind.RIVAL,
        note_prefill='Some origin',
        instruction='Name this Rival',
    )

    specs = pending.input_specs(_projection())

    assert len(specs) == 2
    assert isinstance(specs[0], TextEntry) and specs[0].name == 'name'
    assert isinstance(specs[1], TextEntry) and specs[1].name == 'note'
    assert isinstance(specs[1], TextEntry) and specs[1].value == 'Some origin'

"""Tests for connection event mechanics: handler behaviour, pending ordering."""

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import ConnectionKind
from ceres.character.domain.connection_events import (
    ConnectionsRollHandler,
    PendingConnectionName,
    PendingConnectionsRoll,
)
from ceres.character.domain.sophont import VILANI
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

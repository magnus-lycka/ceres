from collections.abc import Sequence
from typing import TYPE_CHECKING

from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event

if TYPE_CHECKING:
    from ceres.character.domain.character_state import CharacterProjection


def replay(character_id: int, events: Sequence[Event]) -> CharacterProjection:
    if not events:
        raise ReplayError('First event must be a root event (CharacterStartedHandler)')
    projection = events[0].handler.init_replay(character_id, events[0].id)
    if projection is None:
        raise ReplayError('First event must be a root event (CharacterStartedHandler)')
    for event in events[1:]:
        _apply(projection, event)
    return projection


def _apply(projection: CharacterProjection, event: Event) -> None:
    from ceres.character.mechanism.pending_input import PendingInputBase

    fulfilled_pending: PendingInputBase | None = None
    if event.fulfills is not None:
        fulfilled_pending = next((p for p in projection.pending_inputs if p.pending_id == event.fulfills), None)
        projection.fulfill_pending(event)
    elif projection.has_blocking_pending():
        raise ReplayError(
            f'Event {event.id} ({event.kind!r}) submitted while blocking pending input exists: '
            + ', '.join(p.id for p in projection.pending_inputs if p.blocking)
        )
    event.apply(projection, fulfilled_pending)

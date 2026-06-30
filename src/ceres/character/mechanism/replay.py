from collections.abc import Sequence
from typing import Any

from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, PendingInputBase
from ceres.character.mechanism.projection import Projection


def replay(character_id: int, events: Sequence[Event]) -> Any:
    if not events:
        raise ReplayError('First event must be a root event (CharacterCreatedHandler)')
    projection = events[0].handler.init_replay(character_id, events[0].id)
    if projection is None:
        raise ReplayError('First event must be a root event (CharacterCreatedHandler)')
    for event in events[1:]:
        _apply(projection, event)
    return projection


def _apply(projection: Projection, event: Event) -> None:
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

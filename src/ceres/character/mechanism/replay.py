from collections.abc import Sequence

from ceres.character.domain.character_start import CharacterStartedHandler, PendingUcp
from ceres.character.mechanism.character_state import CharacterProjection, CharacterSummary
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event


def replay(character_id: int, events: Sequence[Event]) -> CharacterProjection:
    if not events or not isinstance(events[0].handler, CharacterStartedHandler):
        raise ReplayError('First event must be CharacterStartedEvent')
    first = events[0]
    handler = first.handler
    if not isinstance(handler, CharacterStartedHandler):
        raise TypeError('Replay must start with CharacterStartedHandler')
    projection = CharacterProjection(
        character_id=character_id,
        summary=CharacterSummary(
            name=handler.name,
            sophont=handler.sophont,
            homeworld=handler.homeworld,
            birthworld=handler.homeworld,
        ),
    )
    stat_names = (
        [s.value for s in handler.sophont.ucp_stats] if handler.sophont else ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC']
    )
    projection.pending_inputs.append(
        PendingUcp(pending_id=(first.id, 0), instruction='Provide characteristics (UCP)', stat_names=stat_names)
    )
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

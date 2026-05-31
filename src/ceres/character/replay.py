from collections.abc import Sequence

from ceres.character.events import AnyEvent, CharacterStartedEvent
from ceres.character.projection import (
    AnyPending,
    CharacterProjection,
    CharacterSummary,
    PendingUcp,
    ReplayError,
)


def replay(character_id: int, events: Sequence[AnyEvent]) -> CharacterProjection:
    if not events or not isinstance(events[0], CharacterStartedEvent):
        raise ReplayError('First event must be CharacterStartedEvent')
    first = events[0]
    projection = CharacterProjection(
        character_id=character_id,
        summary=CharacterSummary(
            name=first.name,
            sophont=first.sophont,
            homeworld=first.homeworld,
        ),
    )
    stat_names = (
        [s.value for s in first.sophont.ucp_stats] if first.sophont else ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC']
    )
    projection.pending_inputs.append(
        PendingUcp(id=f'{first.id}.0', instruction='Provide characteristics (UCP)', stat_names=stat_names)
    )
    for event in events[1:]:
        _apply(projection, event)
    return projection


def _apply(projection: CharacterProjection, event: AnyEvent) -> None:
    fulfilled_pending: AnyPending | None = None
    if event.fulfills is not None:
        fulfilled_pending = next((p for p in projection.pending_inputs if p.id == event.fulfills), None)
        projection.fulfill_pending(event)
    elif projection.has_blocking_pending():
        raise ReplayError(
            f'Event {event.id} ({event.kind!r}) submitted while blocking pending input exists: '
            + ', '.join(p.id for p in projection.pending_inputs if p.blocking)
        )
    event.apply(projection, fulfilled_pending)

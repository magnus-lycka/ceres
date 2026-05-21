from ceres.character.characteristics import UCP_STATS
from ceres.character.events import AnyEvent, CharacterStartedEvent, UcpEvent
from ceres.character.projection import CharacterProjection, CharacterSummary, PendingInput


class ReplayError(Exception):
    pass


def replay(character_id: int, events: list[AnyEvent]) -> CharacterProjection:
    projection = CharacterProjection(character_id=character_id)

    for event in events:
        _apply(projection, event)

    return projection


def _apply(projection: CharacterProjection, event: AnyEvent) -> None:
    if event.fulfills is not None:
        _fulfill(projection, event)
    elif _has_blocking_pending(projection):
        raise ReplayError(
            f'Event {event.id} ({event.kind!r}) submitted while blocking pending input exists: '
            + ', '.join(p.id for p in projection.pending_inputs if p.blocking)
        )

    match event:
        case CharacterStartedEvent():
            _apply_character_started(projection, event)
        case UcpEvent():
            _apply_ucp(projection, event)


def _fulfill(projection: CharacterProjection, event: AnyEvent) -> None:
    fulfills = event.fulfills
    matched = next((p for p in projection.pending_inputs if p.id == fulfills), None)
    if matched is None:
        raise ReplayError(f'Event {event.id} ({event.kind!r}) references unknown pending input {fulfills!r}')
    projection.pending_inputs.remove(matched)


def _has_blocking_pending(projection: CharacterProjection) -> bool:
    return any(p.blocking for p in projection.pending_inputs)


def _apply_character_started(projection: CharacterProjection, event: CharacterStartedEvent) -> None:
    projection.summary = CharacterSummary(name=event.name, species=event.sophont)
    projection.pending_inputs.append(
        PendingInput(id=f'{event.id}.0', kind='ucp', instruction='Provide characteristics (UCP)')
    )


def _apply_ucp(projection: CharacterProjection, event: UcpEvent) -> None:
    projection.summary.characteristics = _parse_ucp(event.ucp)


def _parse_ucp(ucp: str) -> dict[str, int]:
    if len(ucp) != 6:
        raise ReplayError(f'Invalid UCP: {ucp!r} — expected 6 hex digits')
    return {stat: int(digit, 16) for stat, digit in zip(UCP_STATS, ucp, strict=True)}

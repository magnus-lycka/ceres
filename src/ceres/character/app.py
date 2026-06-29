from pathlib import Path

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.character_start import CharacterStartedHandler
from ceres.character.domain.character_state import CharacterSummary
from ceres.character.domain.event_handlers import register_event_handlers
from ceres.character.domain.sophont import Sophont
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.store import SqliteCharacterBackend


def create_backend(database: str | Path | None = None) -> SqliteCharacterBackend:
    return SqliteCharacterBackend(
        database=database,
        ensure_handlers_registered=register_event_handlers,
        summary_from_json=CharacterSummary.model_validate_json,
    )


def make_start_event(sophont: Sophont, homeworld: TravellerMapWorld, player: str, name: str) -> Event:
    return Event(handler=CharacterStartedHandler(sophont=sophont, homeworld=homeworld, player=player, name=name))

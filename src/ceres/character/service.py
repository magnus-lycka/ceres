"""CharacterService — the domain façade for all character operations."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ceres.character.domain.character_start import CharacterCreatedHandler
from ceres.character.domain.character_state import CharacterSummary
from ceres.character.domain.event_handlers import register_event_handlers
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.store import SqliteCharacterBackend


@dataclass
class CharacterListItem:
    id: int
    name: str
    player: str
    sophont: str


class CharacterService:
    def __init__(self, database: str | Path | None = None):
        self._backend: SqliteCharacterBackend = SqliteCharacterBackend(
            database=database,
            ensure_handlers_registered=register_event_handlers,
            summary_from_json=CharacterSummary.model_validate_json,
        )

    def create_character(self, name: str, player: str) -> int:
        ev = Event(handler=CharacterCreatedHandler(name=name, player=player))
        row = self._backend.start([ev], player=player, name=name)
        return row['id']

    def list_characters(self) -> list[CharacterListItem]:
        return [
            CharacterListItem(id=r['id'], name=r['name'], player=r['player'], sophont=r['sophont'])
            for r in self._backend.list_characters()
        ]

    def get_summary(self, character_id: int) -> Any | None:
        return self._backend.get_summary(character_id)

    def get_projection(self, character_id: int) -> Any | None:
        return self._backend.get_projection(character_id)

    def submit_event(self, character_id: int, fulfills: str, form_data: dict[str, str]) -> None:
        projection = self._backend.get_projection(character_id)
        if projection is None:
            raise ValueError(f'Character {character_id} not found')
        parts = fulfills.split('.')
        if len(parts) == 2 and parts[0].lstrip('-').isdigit() and parts[1].lstrip('-').isdigit():
            pending_id: tuple[int, int] | str = (int(parts[0]), int(parts[1]))
        else:
            pending_id = fulfills
        pending = next((p for p in projection.pending_inputs if p.pending_id == pending_id), None)
        if pending is None:
            raise ValueError(f'No pending input with id={fulfills!r}')
        event = pending.event_from_form(form_data)
        self._backend.append_event(character_id, event)

    def delete_character(self, character_id: int) -> None:
        self._backend.delete_character(character_id)

    def rename_character(self, character_id: int, name: str) -> bool:
        result = self._backend.rename_character(character_id, name)
        return result is not None

    def close(self) -> None:
        self._backend.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()

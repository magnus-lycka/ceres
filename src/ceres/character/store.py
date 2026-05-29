import json
from pathlib import Path
import sqlite3
from typing import TypedDict

from pydantic import TypeAdapter

from ceres import settings
from ceres.character.events import AnyEvent, CharacterStartedEvent
from ceres.character.projection import CharacterProjection
from ceres.character.replay import replay

_event_adapter: TypeAdapter[AnyEvent] = TypeAdapter(AnyEvent)


class CharacterRow(TypedDict):
    id: int
    sophont: str
    player: str
    name: str


class SqliteCharacterBackend:
    def __init__(self, database: str | Path | None = None):
        if database is None:
            database = settings.data_dir() / 'characters.sqlite'
        if database != ':memory:':
            Path(database).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(database, check_same_thread=False)
        self.connection.execute(
            'create table if not exists characters ('
            'id integer primary key, '
            'sophont text not null, '
            'player text not null, '
            'name text not null, '
            "events_json text not null default '[]')"
        )
        self._ensure_column('events_json', "text not null default '[]'")

    def _ensure_column(self, column: str, definition: str) -> None:
        columns = {row[1] for row in self.connection.execute('pragma table_info(characters)')}
        if column not in columns:
            self.connection.execute(f'alter table characters add column {column} {definition}')

    def start(self, *, sophont: str, player: str, name: str) -> CharacterRow:
        cursor = self.connection.execute(
            'insert into characters (sophont, player, name) values (?, ?, ?)',
            (sophont, player, name),
        )
        self.connection.commit()
        character_id = cursor.lastrowid
        if character_id is None:
            raise RuntimeError('SQLite did not return a character id')
        row: CharacterRow = {'id': character_id, 'sophont': sophont, 'player': player, 'name': name}
        self.append_event(character_id, CharacterStartedEvent(sophont=sophont, player=player, name=name))
        return row

    def list_characters(self) -> list[CharacterRow]:
        cursor = self.connection.execute('select id, sophont, player, name from characters order by id')
        return [{'id': r[0], 'sophont': r[1], 'player': r[2], 'name': r[3]} for r in cursor]

    def get_character(self, character_id: int) -> CharacterRow | None:
        cursor = self.connection.execute(
            'select id, sophont, player, name from characters where id = ?',
            (character_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return {'id': row[0], 'sophont': row[1], 'player': row[2], 'name': row[3]}

    def rename_character(self, character_id: int, name: str) -> CharacterRow | None:
        character = self.get_character(character_id)
        if character is None:
            return None
        self.connection.execute('update characters set name = ? where id = ?', (name, character_id))
        self.connection.commit()
        character['name'] = name
        return character

    def append_event(self, character_id: int, event: AnyEvent) -> AnyEvent:
        event, _projection = self.append_event_with_projection(character_id, event)
        return event

    def append_event_with_projection(self, character_id: int, event: AnyEvent) -> tuple[AnyEvent, CharacterProjection]:
        events = self.load_typed_events(character_id) or []
        event = event.model_copy(update={'id': len(events) + 1})
        candidate = [*events, event]
        projection = replay(character_id, candidate)  # raises ReplayError if invalid; do not save
        self._save_events(character_id, candidate)
        return event, projection

    def load_typed_events(self, character_id: int) -> list[AnyEvent] | None:
        cursor = self.connection.execute('select events_json from characters where id = ?', (character_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        return [_event_adapter.validate_python(e) for e in data]

    def get_projection(self, character_id: int) -> CharacterProjection | None:
        events = self.load_typed_events(character_id)
        if events is None:
            return None
        return replay(character_id, events)

    def _save_events(self, character_id: int, events: list[AnyEvent]) -> None:
        serialized = json.dumps([e.model_dump() for e in events])
        self.connection.execute('update characters set events_json = ? where id = ?', (serialized, character_id))
        self.connection.commit()

    def delete_character(self, character_id: int) -> CharacterRow | None:
        character = self.get_character(character_id)
        if character is None:
            return None
        self.connection.execute('delete from characters where id = ?', (character_id,))
        self.connection.commit()
        return character

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()

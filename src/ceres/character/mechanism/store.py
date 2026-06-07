import json
from pathlib import Path
import sqlite3
from typing import TypedDict

from pydantic import TypeAdapter

from ceres import settings
from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.character_start import CharacterStartedHandler
from ceres.character.domain.sophont import Sophont
from ceres.character.mechanism.character_state import CharacterProjection
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay

_event_adapter: TypeAdapter[Event] = TypeAdapter(Event)


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
            'name text not null)'
        )
        self.connection.execute(
            'create table if not exists character_events ('
            'character_id integer not null references characters(id), '
            'id integer not null, '
            'payload text not null, '
            'primary key (character_id, id))'
        )

    def start(self, *, sophont: Sophont, homeworld: TravellerMapWorld, player: str, name: str) -> CharacterRow:
        cursor = self.connection.execute(
            'insert into characters (sophont, player, name) values (?, ?, ?)',
            (sophont.name, player, name),
        )
        self.connection.commit()
        character_id = cursor.lastrowid
        if character_id is None:
            raise RuntimeError('SQLite did not return a character id')
        row: CharacterRow = {'id': character_id, 'sophont': sophont.name, 'player': player, 'name': name}
        self.append_event(
            character_id,
            Event(handler=CharacterStartedHandler(sophont=sophont, homeworld=homeworld, player=player, name=name)),
        )
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

    def append_event(self, character_id: int, event: Event) -> Event:
        event, _projection = self.append_event_with_projection(character_id, event)
        return event

    def append_event_with_projection(self, character_id: int, event: Event) -> tuple[Event, CharacterProjection]:
        events = self.load_typed_events(character_id) or []
        event = event.model_copy(update={'id': len(events) + 1})
        candidate = [*events, event]
        projection = replay(character_id, candidate)  # raises ReplayError if invalid; do not save
        self.connection.execute(
            'insert into character_events (character_id, id, payload) values (?, ?, ?)',
            (character_id, event.id, json.dumps(event.model_dump())),
        )
        self.connection.commit()
        return event, projection

    def load_typed_events(self, character_id: int) -> list[Event] | None:
        cursor = self.connection.execute(
            'select payload from character_events where character_id = ? order by id',
            (character_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        return [_event_adapter.validate_python(json.loads(r[0])) for r in rows]

    def get_projection(self, character_id: int) -> CharacterProjection | None:
        events = self.load_typed_events(character_id)
        if events is None:
            return None
        return replay(character_id, events)

    def delete_character(self, character_id: int) -> CharacterRow | None:
        character = self.get_character(character_id)
        if character is None:
            return None
        self.connection.execute('delete from character_events where character_id = ?', (character_id,))
        self.connection.execute('delete from characters where id = ?', (character_id,))
        self.connection.commit()
        return character

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()

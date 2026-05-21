import json
from pathlib import Path
import re
import sqlite3
from typing import TypedDict

from pydantic import TypeAdapter

from ceres import settings
from ceres.character.characteristics import UCP_STATS
from ceres.character.events import AnyEvent, CharacterStartedEvent, UcpEvent
from ceres.character.projection import CharacterProjection
from ceres.character.replay import replay

UCP_CHANGE_PATTERN = re.compile(r'^([A-Z]{3})(?:(=)(\d+)|([+-])(\d+))$')
UCP_SHORT_PATTERN = re.compile(r'^[0-9A-F]{6}$')

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
            "ucp_json text not null default '{}', "
            "events_json text not null default '[]')"
        )
        self._ensure_column('ucp_json', "text not null default '{}'")
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
        events = self.load_typed_events(character_id) or []
        event = event.model_copy(update={'id': len(events) + 1})
        candidate = [*events, event]
        replay(character_id, candidate)  # raises ReplayError if invalid; do not save
        self._save_events(character_id, candidate)
        return event

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

    def get_ucp(self, character_id: int) -> dict[str, int] | None:
        projection = self.get_projection(character_id)
        if projection is None:
            return None
        return dict(projection.summary.characteristics)

    def patch_ucp(self, character_id: int, changes: list[str]) -> dict[str, int] | None:
        projection = self.get_projection(character_id)
        if projection is None:
            return None
        current = dict(projection.summary.characteristics)
        for change in expand_ucp_changes(changes):
            stat, operation, value = parse_ucp_change(change)
            if operation == 'set':
                current[stat] = value
            else:
                current[stat] = current.get(stat, 0) + value
        new_ucp = ''.join(f'{current.get(stat, 0):X}' for stat in UCP_STATS)
        ucp_pending = next(
            (p for p in projection.pending_inputs if p.kind == 'ucp' and p.blocking),
            None,
        )
        self.append_event(character_id, UcpEvent(ucp=new_ucp, fulfills=ucp_pending.id if ucp_pending else None))
        return {stat: int(digit, 16) for stat, digit in zip(UCP_STATS, new_ucp, strict=True)}

    def delete_character(self, character_id: int) -> CharacterRow | None:
        character = self.get_character(character_id)
        if character is None:
            return None
        self.connection.execute('delete from characters where id = ?', (character_id,))
        self.connection.commit()
        return character

    def list_events(self, character_id: int) -> list[AnyEvent] | None:
        return self.load_typed_events(character_id)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()


def parse_ucp_change(change: str) -> tuple[str, str, int]:
    match = UCP_CHANGE_PATTERN.match(change)
    if not match:
        raise ValueError(f'Invalid UCP change: {change}')
    stat = match.group(1)
    if stat not in UCP_STATS:
        raise ValueError(f'Invalid UCP change: {change}')
    if match.group(2) == '=':
        return stat, 'set', int(match.group(3))
    sign = 1 if match.group(4) == '+' else -1
    return stat, 'adjust', sign * int(match.group(5))


def expand_ucp_changes(changes: list[str]) -> list[str]:
    expanded: list[str] = []
    for change in changes:
        if UCP_SHORT_PATTERN.match(change):
            expanded.extend(f'{stat}={int(value, 16)}' for stat, value in zip(UCP_STATS, change, strict=True))
        else:
            expanded.append(change)
    return expanded

import json
from pathlib import Path
import re
import sqlite3
from typing import TypedDict

from ceres import settings


class CharacterRow(TypedDict):
    id: int
    sophont: str
    player: str
    name: str


class CharacterEvent(TypedDict):
    kind: str
    changes: list[str]
    note: str | None


UCP_STATS = ('STR', 'DEX', 'END', 'INT', 'EDU', 'SOC')
UCP_CHANGE_PATTERN = re.compile(r'^([A-Z]{3})(?:(=)(\d+)|([+-])(\d+))$')
UCP_SHORT_PATTERN = re.compile(r'^[0-9A-F]{6}$')


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
        return {'id': character_id, 'sophont': sophont, 'player': player, 'name': name}

    def list_characters(self) -> list[CharacterRow]:
        cursor = self.connection.execute('select id, sophont, player, name from characters order by id')
        return [{'id': row[0], 'sophont': row[1], 'player': row[2], 'name': row[3]} for row in cursor]

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

    def get_ucp(self, character_id: int) -> dict[str, int] | None:
        cursor = self.connection.execute('select ucp_json from characters where id = ?', (character_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        data = json.loads(row[0])
        return {stat: int(value) for stat, value in data.items()}

    def patch_ucp(self, character_id: int, changes: list[str], note: str | None = None) -> dict[str, int] | None:
        ucp = self.get_ucp(character_id)
        if ucp is None:
            return None
        for change in expand_ucp_changes(changes):
            stat, operation, value = parse_ucp_change(change)
            if operation == 'set':
                ucp[stat] = value
            else:
                ucp[stat] = ucp.get(stat, 0) + value
        events = self.list_events(character_id)
        if events is None:
            return None
        events.append({'kind': 'ucp_changed', 'changes': changes, 'note': note})
        self.connection.execute(
            'update characters set ucp_json = ?, events_json = ? where id = ?',
            (json.dumps(ucp), json.dumps(events), character_id),
        )
        self.connection.commit()
        return ucp

    def list_events(self, character_id: int) -> list[CharacterEvent] | None:
        cursor = self.connection.execute('select events_json from characters where id = ?', (character_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return json.loads(row[0])

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

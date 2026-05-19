from pathlib import Path
import sqlite3
from typing import TypedDict

from ceres import settings


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

    def close(self) -> None:
        self.connection.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()

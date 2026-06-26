from pathlib import Path
import sqlite3
import subprocess
import sys
import textwrap

import pytest

from ceres.character.domain.career import CITIZEN
from ceres.character.domain.career.entry import CareerEntryHandler
from ceres.character.domain.character_start import PendingUcp, UcpHandler
from ceres.character.domain.sophont import HUMANITI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.store import SqliteCharacterBackend
from tests.unit.character.helpers import MOCK_WORLD


def _append_ucp(backend: SqliteCharacterBackend, character_id: int, ucp: str) -> None:
    projection = backend.get_projection(character_id)
    assert projection is not None
    pending = next(p for p in projection.pending_inputs if isinstance(p, PendingUcp))
    backend.append_event(character_id, Event(fulfills=pending.pending_id, handler=UcpHandler(ucp=ucp)))


def test_store_persists_latest_character_summary() -> None:
    with SqliteCharacterBackend(':memory:') as backend:
        row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Stored')
        _append_ucp(backend, row['id'], '89A67B')

        summary = backend.get_summary(row['id'])

        assert summary is not None
        assert summary.name == 'Stored'
        assert summary.ucp == '89A67B'


def test_rollback_updates_persisted_character_summary() -> None:
    with SqliteCharacterBackend(':memory:') as backend:
        row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Stored')
        _append_ucp(backend, row['id'], '89A67B')

        assert backend.rollback_last_event(row['id'])

        summary = backend.get_summary(row['id'])
        assert summary is not None
        assert summary.ucp is None


def test_store_adds_summary_column_to_legacy_database(tmp_path: Path) -> None:
    database = tmp_path / 'legacy.sqlite'
    connection = sqlite3.connect(database)
    connection.execute(
        'create table characters ('
        'id integer primary key, sophont text not null, player text not null, name text not null)'
    )
    connection.commit()
    connection.close()

    with SqliteCharacterBackend(database) as backend:
        columns = {row[1] for row in backend.connection.execute('pragma table_info(characters)')}

    assert 'summary' in columns


def test_store_backfills_missing_legacy_summary(tmp_path: Path) -> None:
    database = tmp_path / 'legacy.sqlite'
    with SqliteCharacterBackend(database) as backend:
        row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Legacy')
        backend.connection.execute('update characters set summary = null where id = ?', (row['id'],))
        backend.connection.commit()

    with SqliteCharacterBackend(database) as backend:
        summary = backend.get_summary(row['id'])

    assert summary is not None
    assert summary.name == 'Legacy'


def test_store_loads_career_event_in_a_fresh_process(tmp_path: Path) -> None:
    payload = Event(
        handler=CareerEntryHandler(
            career=CITIZEN,
            assignment=CITIZEN.assignment('Corporate'),
            qualification_roll=9,
        ),
    ).model_dump_json()
    script = textwrap.dedent(
        """
        import sys

        from ceres.character.mechanism.store import SqliteCharacterBackend

        backend = SqliteCharacterBackend(sys.argv[1])
        backend.connection.execute(
            'insert into events (character_id, id, payload) values (?, ?, ?)',
            (1, 1, sys.argv[2]),
        )
        event = backend.load_typed_events(1)[0]
        assert type(event.handler).__name__ == 'CareerEntryHandler'
        """
    )

    result = subprocess.run(
        [sys.executable, '-c', script, str(tmp_path / 'characters.sqlite'), payload],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_get_summary_returns_none_for_nonexistent_character() -> None:
    with SqliteCharacterBackend(':memory:') as backend:
        assert backend.get_summary(9999) is None


def test_rename_character_updates_name_and_summary() -> None:
    with SqliteCharacterBackend(':memory:') as backend:
        row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='Test', name='Old')

        result = backend.rename_character(row['id'], 'New')

        assert result is not None
        assert result['name'] == 'New'
        summary = backend.get_summary(row['id'])
        assert summary is not None
        assert summary.name == 'New'


def test_rename_character_returns_none_for_nonexistent_character() -> None:
    with SqliteCharacterBackend(':memory:') as backend:
        assert backend.rename_character(9999, 'Whatever') is None


def test_rollback_returns_false_when_no_events() -> None:
    with SqliteCharacterBackend(':memory:') as backend:
        assert not backend.rollback_last_event(9999)


def test_backfill_skips_character_with_no_events() -> None:
    with SqliteCharacterBackend(':memory:') as backend:
        backend.connection.execute(
            "insert into characters (id, sophont, player, name) values (99, 'Humaniti', 'Test', 'Orphan')"
        )
        backend.connection.commit()
        backend._backfill_missing_summaries()
        assert backend.get_summary(99) is None


def test_rollback_rolls_back_db_transaction_on_failure() -> None:
    with SqliteCharacterBackend(':memory:') as backend:
        row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='Test', name='Char')
        backend.connection.execute('drop table characters')
        with pytest.raises(sqlite3.OperationalError):
            backend.rollback_last_event(row['id'])

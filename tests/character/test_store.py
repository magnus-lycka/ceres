from pathlib import Path
import subprocess
import sys
import textwrap

from ceres.character.domain.career import CITIZEN
from ceres.character.domain.career.entry import CareerEntryHandler
from ceres.character.mechanism.event_base import Event


def test_store_loads_career_event_in_a_fresh_process(tmp_path: Path) -> None:
    payload = Event(
        id=1,
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

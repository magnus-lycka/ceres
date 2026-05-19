import pytest
from typer.testing import CliRunner

from ceres.character.cli import app, build_app
from ceres.character.store import SqliteCharacterBackend


@pytest.fixture
def memory_app(tmp_path):
    backend = SqliteCharacterBackend(':memory:')
    try:
        yield build_app(backend=backend, current_path=tmp_path / '.current')
    finally:
        backend.close()


def test_cli_lists_sophonts():
    result = CliRunner().invoke(app, ['sophonts', 'list'])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ['Vilani', 'Humaniti']


def test_cli_starts_character_creation_with_vilani_sophont(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])

    assert result.exit_code == 0
    assert result.stdout.splitlines() == ['Started character creation: Boss']


def test_cli_rejects_unknown_sophont_and_lists_available_sophonts(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'start', '-s', 'UnknownAlien', 'Boss'])

    assert result.exit_code != 0
    assert 'Unknown sophont: UnknownAlien' in result.output
    assert 'Available sophonts: Vilani, Humaniti' in result.output


def test_cli_lists_started_character_creations(memory_app):
    test_app = memory_app
    runner = CliRunner()

    first = runner.invoke(test_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    second = runner.invoke(test_app, ['create', 'start', '-s', 'Humaniti', '-p', 'Anders', 'Lynn Rashid'])
    listed = runner.invoke(test_app, ['create', 'list'])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert listed.exit_code == 0
    assert listed.stdout.splitlines() == [
        '*  Id  Sophont   Player  Name',
        '   1   Vilani    NPC     Boss',
        '*  2   Humaniti  Anders  Lynn Rashid',
    ]


def test_cli_tracks_current_character_creation(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    current_after_first = runner.invoke(memory_app, ['create', 'current'])
    runner.invoke(memory_app, ['create', 'start', '-s', 'Humaniti', '-p', 'Anders', 'Lynn Rashid'])
    current_after_second = runner.invoke(memory_app, ['create', 'current'])
    use_first = runner.invoke(memory_app, ['create', 'use', '1'])
    current_after_use = runner.invoke(memory_app, ['create', 'current'])
    listed_after_use = runner.invoke(memory_app, ['create', 'list'])

    assert current_after_first.exit_code == 0
    assert current_after_first.stdout.splitlines() == ['1 Vilani NPC Boss']
    assert current_after_second.exit_code == 0
    assert current_after_second.stdout.splitlines() == ['2 Humaniti Anders Lynn Rashid']
    assert use_first.exit_code == 0
    assert use_first.stdout.splitlines() == ['Current character creation: Boss']
    assert current_after_use.exit_code == 0
    assert current_after_use.stdout.splitlines() == ['1 Vilani NPC Boss']
    assert listed_after_use.exit_code == 0
    assert listed_after_use.stdout.splitlines() == [
        '*  Id  Sophont   Player  Name',
        '*  1   Vilani    NPC     Boss',
        '   2   Humaniti  Anders  Lynn Rashid',
    ]


def test_cli_current_character_is_local_to_current_file(tmp_path):
    backend = SqliteCharacterBackend(':memory:')
    try:
        first_app = build_app(backend=backend, current_path=tmp_path / 'first' / '.current')
        second_app = build_app(backend=backend, current_path=tmp_path / 'second' / '.current')
        runner = CliRunner()

        runner.invoke(first_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
        runner.invoke(first_app, ['create', 'start', '-s', 'Humaniti', '-p', 'Anders', 'Lynn Rashid'])
        runner.invoke(first_app, ['create', 'use', '1'])
        second_current = runner.invoke(second_app, ['create', 'current'])

        assert second_current.exit_code != 0
        assert 'No current character creation' in second_current.output

        runner.invoke(second_app, ['create', 'use', '2'])
        first_current = runner.invoke(first_app, ['create', 'current'])
        second_current = runner.invoke(second_app, ['create', 'current'])

        assert first_current.exit_code == 0
        assert first_current.stdout.splitlines() == ['1 Vilani NPC Boss']
        assert second_current.exit_code == 0
        assert second_current.stdout.splitlines() == ['2 Humaniti Anders Lynn Rashid']
    finally:
        backend.close()


def test_cli_rejects_unknown_current_character_id(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'use', '999'])

    assert result.exit_code != 0
    assert 'Unknown character creation id: 999' in result.output


def test_cli_renames_current_character_creation(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    renamed = runner.invoke(memory_app, ['create', 'rename', 'Flavius Rupert'])
    current = runner.invoke(memory_app, ['create', 'current'])
    listed = runner.invoke(memory_app, ['create', 'list'])

    assert renamed.exit_code == 0
    assert renamed.stdout.splitlines() == ['Renamed character creation: Flavius Rupert']
    assert current.exit_code == 0
    assert current.stdout.splitlines() == ['1 Vilani NPC Flavius Rupert']
    assert listed.exit_code == 0
    assert listed.stdout.splitlines() == [
        '*  Id  Sophont   Player  Name',
        '*  1   Vilani    NPC     Flavius Rupert',
    ]


def test_cli_rejects_rename_without_current_character(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'rename', 'Flavius Rupert'])

    assert result.exit_code != 0
    assert 'No current character creation' in result.output


def test_cli_rejects_empty_rename(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    result = runner.invoke(memory_app, ['create', 'rename', ''])

    assert result.exit_code != 0
    assert 'Name must not be empty' in result.output


def test_cli_requires_character_name_when_starting_creation(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'start', '-s', 'Vilani', ''])

    assert result.exit_code != 0
    assert 'Name must not be empty' in result.output

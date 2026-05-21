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


def test_cli_lists_skills():
    result = CliRunner().invoke(app, ['skills', 'list'])

    assert result.exit_code == 0
    lines = result.stdout.splitlines()
    assert 'Admin' in lines
    assert 'Animals: Handling, Veterinary, Training' in lines
    assert 'Art' not in lines
    assert 'Creative Art: Visual Media, Exotic Media' in lines
    assert 'Profession' not in lines
    assert (
        'Worker Profession: Armourer, Biologicals, Civil Engineering, Construction, Hydroponics, Metalworking, Polymers'
        in lines
    )
    assert 'Science' not in lines
    assert 'Space Science: Astronomy, Cosmology, Planetology' in lines


def test_cli_starts_character_creation_with_vilani_sophont(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])

    assert result.exit_code == 0
    assert result.stdout.splitlines()[0] == 'Started character creation: Boss'
    assert 'Pending:' in result.stdout


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
        '*  Id  Sophont   UCP     Player  Name',
        '   1   Vilani            NPC     Boss',
        '*  2   Humaniti          Anders  Lynn Rashid',
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
        '*  Id  Sophont   UCP     Player  Name',
        '*  1   Vilani            NPC     Boss',
        '   2   Humaniti          Anders  Lynn Rashid',
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


def test_cli_shows_current_character_creation(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    shown = runner.invoke(memory_app, ['create', 'show'])

    assert shown.exit_code == 0
    assert shown.stdout.splitlines() == [
        'Id: 1',
        'Sophont: Vilani',
        'Player: NPC',
        'Name: Boss',
    ]


def test_cli_shows_character_creation_by_id(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    runner.invoke(memory_app, ['create', 'start', '-s', 'Humaniti', '-p', 'Anders', 'Lynn Rashid'])
    shown = runner.invoke(memory_app, ['create', 'show', '1'])

    assert shown.exit_code == 0
    assert shown.stdout.splitlines() == [
        'Id: 1',
        'Sophont: Vilani',
        'Player: NPC',
        'Name: Boss',
    ]


def test_cli_show_includes_ucp(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    runner.invoke(memory_app, ['create', 'ucp', '7869A5'])
    shown = runner.invoke(memory_app, ['create', 'show'])

    assert shown.exit_code == 0
    assert shown.stdout.splitlines() == [
        'Id: 1',
        'Sophont: Vilani',
        'Player: NPC',
        'Name: Boss',
        'UCP: 7869A5',
        'Characteristics: STR 7 DEX 8 END 6 INT 9 EDU 10 SOC 5',
    ]


def test_cli_rejects_show_without_current_character(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'show'])

    assert result.exit_code != 0
    assert 'No current character creation' in result.output


def test_cli_rejects_show_for_unknown_character(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'show', '999'])

    assert result.exit_code != 0
    assert 'Unknown character creation id: 999' in result.output


def test_cli_sets_and_shows_current_ucp(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    changed = runner.invoke(memory_app, ['create', 'ucp', 'STR=7', 'DEX=8', 'END=6', 'INT=9', 'EDU=10', 'SOC=5'])
    shown = runner.invoke(memory_app, ['create', 'ucp'])

    assert changed.exit_code == 0
    assert changed.stdout.splitlines() == ['STR 7 DEX 8 END 6 INT 9 EDU 10 SOC 5']
    assert shown.exit_code == 0
    assert shown.stdout.splitlines() == ['STR 7 DEX 8 END 6 INT 9 EDU 10 SOC 5']


def test_cli_sets_current_ucp_from_short_form(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    changed = runner.invoke(memory_app, ['create', 'ucp', '7788B4'])
    shown = runner.invoke(memory_app, ['create', 'ucp'])
    listed = runner.invoke(memory_app, ['create', 'list'])

    assert changed.exit_code == 0
    assert changed.stdout.splitlines() == ['STR 7 DEX 7 END 8 INT 8 EDU 11 SOC 4']
    assert shown.exit_code == 0
    assert shown.stdout.splitlines() == ['STR 7 DEX 7 END 8 INT 8 EDU 11 SOC 4']
    assert listed.exit_code == 0
    assert listed.stdout.splitlines() == [
        '*  Id  Sophont   UCP     Player  Name',
        '*  1   Vilani    7788B4  NPC     Boss',
    ]


def test_cli_lists_ucp_short_form(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    runner.invoke(memory_app, ['create', 'ucp', 'STR=7', 'DEX=8', 'END=6', 'INT=9', 'EDU=10', 'SOC=5'])
    listed = runner.invoke(memory_app, ['create', 'list'])

    assert listed.exit_code == 0
    assert listed.stdout.splitlines() == [
        '*  Id  Sophont   UCP     Player  Name',
        '*  1   Vilani    7869A5  NPC     Boss',
    ]


def test_cli_patches_current_ucp_with_adjustments(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    runner.invoke(memory_app, ['create', 'ucp', 'STR=7', 'DEX=8'])
    changed = runner.invoke(memory_app, ['create', 'ucp', 'STR-2', 'DEX-1', 'EDU+1'])

    assert changed.exit_code == 0
    assert 'STR 5' in changed.stdout
    assert 'DEX 7' in changed.stdout
    assert 'EDU 1' in changed.stdout


def test_cli_rejects_ucp_without_current_character(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'ucp'])

    assert result.exit_code != 0
    assert 'No current character creation' in result.output


def test_cli_rejects_invalid_ucp_change(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    result = runner.invoke(memory_app, ['create', 'ucp', 'FOO=7'])

    assert result.exit_code != 0
    assert 'Invalid UCP change: FOO=7' in result.output


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
        '*  Id  Sophont   UCP     Player  Name',
        '*  1   Vilani            NPC     Flavius Rupert',
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


def test_cli_deletes_current_character(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', '-s', 'Vilani', 'Boss'])
    runner.invoke(memory_app, ['create', 'start', '-s', 'Humaniti', 'Lynn'])
    result = runner.invoke(memory_app, ['create', 'delete', '1'])
    listed = runner.invoke(memory_app, ['create', 'list'])

    assert result.exit_code == 0
    assert 'Deleted' in result.stdout
    assert 'Boss' in result.stdout
    assert 'Lynn' in listed.stdout
    assert 'Boss' not in listed.stdout


def test_cli_rejects_delete_for_unknown_character(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'delete', '999'])

    assert result.exit_code != 0
    assert 'Unknown character creation id: 999' in result.output

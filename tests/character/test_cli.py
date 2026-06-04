import pytest
from typer.testing import CliRunner

from ceres.character import skills as character_skills
from ceres.character.benefits import LAB_SHIP, SHIP_SHARE
from ceres.character.careers import SCOUT
from ceres.character.characteristics import Chars
from ceres.character.cli import (
    _expand_ucp_changes,
    _format_skill,
    _parse_ucp_change,
    app,
    build_app,
    read_current_id,
    render_character,
    render_character_show,
    render_pending_inputs,
    render_projection_summary,
    render_ucp,
    render_ucp_short,
    write_current_id,
)
from ceres.character.events import AnyEvent, PendingBackgroundSkills, PendingUcp
from ceres.character.replay import ReplayError
from ceres.character.sophonts import VILANI
from ceres.character.state import (
    CharacterProjection,
    CharacterSummary,
    Contact,
)
from ceres.character.store import CharacterRow, SqliteCharacterBackend
from tests.character.helpers import MOCK_WORLD


class ProjectionlessBackend(SqliteCharacterBackend):
    def get_projection(self, character_id: int) -> CharacterProjection | None:
        return None


class ReplayErrorBackend(SqliteCharacterBackend):
    fail_append: bool = False

    def append_event(self, character_id: int, event: AnyEvent) -> AnyEvent:
        if self.fail_append:
            raise ReplayError('synthetic replay failure')
        return super().append_event(character_id, event)


@pytest.fixture
def memory_app(tmp_path, monkeypatch):
    monkeypatch.setattr('ceres.character.cli.fetch_world', lambda s, h: MOCK_WORLD)
    backend = SqliteCharacterBackend(':memory:')
    try:
        yield build_app(backend=backend, current_path=tmp_path / '.current')
    finally:
        backend.close()


def _start_vilani(runner: CliRunner, app, name: str = 'Boss', player: str = 'NPC') -> None:
    """Start a character with sophont=Vilani and a mock homeworld in one command."""
    player_args = ['-p', player] if player != 'NPC' else []
    runner.invoke(app, ['create', 'start', *player_args, name, 'Vilani', 'Troj', '2715'])


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


def test_parse_ucp_change_accepts_set_and_adjustments():
    assert _parse_ucp_change('STR=7') == (Chars.STR, 'set', 7)
    assert _parse_ucp_change('EDU+2') == (Chars.EDU, 'adjust', 2)
    assert _parse_ucp_change('SOC-1') == (Chars.SOC, 'adjust', -1)


@pytest.mark.parametrize('change', ['FOO=7', 'STR', 'STR++1', 'STR=A'])
def test_parse_ucp_change_rejects_invalid_changes(change):
    with pytest.raises(ValueError) as exc_info:
        _parse_ucp_change(change)
    assert str(exc_info.value) == f'Invalid UCP change: {change}'


def test_expand_ucp_changes_expands_short_form_and_preserves_explicit_changes():
    assert _expand_ucp_changes(['7869A5', 'SOC+1']) == [
        'STR=7',
        'DEX=8',
        'END=6',
        'INT=9',
        'EDU=10',
        'SOC=5',
        'SOC+1',
    ]


def test_current_character_id_file_round_trips(tmp_path):
    current_path = tmp_path / 'nested' / '.current'

    assert read_current_id(current_path) is None
    current_path.parent.mkdir()
    current_path.write_text('\n')
    assert read_current_id(current_path) is None

    write_current_id(current_path, 42)

    assert read_current_id(current_path) == 42
    assert current_path.read_text() == '42\n'


def test_render_character_uses_projection_sophont_name_when_supplied():
    character: CharacterRow = {'id': 7, 'sophont': 'Humaniti', 'player': 'NPC', 'name': 'Boss'}

    assert render_character(character) == '7 Humaniti NPC Boss'
    assert render_character(character, sophont_name='Vilani') == '7 Vilani NPC Boss'


def test_render_character_show_includes_complete_ucp_from_projection():
    character: CharacterRow = {'id': 7, 'sophont': 'Humaniti', 'player': 'NPC', 'name': 'Boss'}
    projection = _projection(
        characteristics={
            Chars.STR: 7,
            Chars.DEX: 8,
            Chars.END: 6,
            Chars.INT: 9,
            Chars.EDU: 10,
            Chars.SOC: 5,
        }
    )

    assert render_character_show(character, projection) == [
        'Id: 7',
        'Sophont: Vilani',
        'Player: NPC',
        'Name: Boss',
        'UCP: 7869A5',
        'Characteristics: STR 7 DEX 8 END 6 INT 9 EDU 10 SOC 5',
    ]


def test_render_ucp_handles_missing_partial_and_complete_values():
    full_ucp = {
        Chars.STR: 7,
        Chars.DEX: 8,
        Chars.END: 6,
        Chars.INT: 9,
        Chars.EDU: 10,
        Chars.SOC: 5,
    }

    assert render_ucp({}) == 'No UCP set'
    assert render_ucp({Chars.STR: 7, Chars.DEX: 8}) == 'STR 7 DEX 8'
    assert render_ucp_short({Chars.STR: 7}) == ''
    assert render_ucp_short(full_ucp) == '7869A5'


def test_format_skill_handles_plain_and_speciality_skills():
    admin = character_skills.Admin(level=character_skills.Level(value=1))
    electronics_all = character_skills.Electronics(
        comms=character_skills.Level(value=1),
        computers=character_skills.Level(value=1),
        remote_ops=character_skills.Level(value=1),
        sensors=character_skills.Level(value=1),
    )
    electronics_mixed = character_skills.Electronics(
        comms=character_skills.Level(value=1),
        sensors=character_skills.Level(value=2),
    )

    assert _format_skill(admin) == ['Admin 1']
    assert _format_skill(electronics_all) == ['Electronics (all)-1']
    assert _format_skill(electronics_mixed) == ['Electronics (Comms)-1', 'Electronics (Sensors)-2']


def test_render_projection_summary_shows_active_character_state():
    projection = _projection(
        current_career=SCOUT,
        current_assignment='Courier',
        rank=1,
        term_count=2,
        characteristics={Chars.STR: 7, Chars.DEX: 8, Chars.END: 6, Chars.INT: 9, Chars.EDU: 10, Chars.SOC: 5},
        skills=[
            character_skills.Admin(level=character_skills.Level(value=1)),
            character_skills.Electronics(sensors=character_skills.Level(value=2)),
        ],
        connections=[Contact(source='mentor')],
        problems=['Enemy made'],
        cash=50000,
        benefits=[LAB_SHIP, SHIP_SHARE],
    )

    assert render_projection_summary(projection) == [
        'Test  (Vilani)  |  Scout / Courier  rank 1  term 2',
        'UCP  7869A5    STR 7  DEX 8  END 6  INT 9  EDU 10  SOC 5',
        'Skills  Admin 1  Electronics (Sensors)-2',
        'Connections  Contact(mentor)',
        'Problem  Enemy made',
        'Cash  Cr50,000',
        'Benefits  Lab Ship  Ship Share',
    ]


def test_render_pending_inputs_marks_blocking_inputs():
    projection = _projection()
    projection.pending_inputs = [
        PendingUcp(id='1.0', instruction='Set UCP'),
        PendingBackgroundSkills(id='1.1', instruction='Optional note', blocking=False),
    ]

    assert render_pending_inputs(projection) == [
        'Pending:',
        '  1.0  PendingUcp [blocking]  — Set UCP',
        '  1.1  PendingBackgroundSkills  — Optional note',
    ]


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


def test_cli_starts_character_creation(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'start', 'Boss', 'Vilani', 'Troj', '2715'])

    assert result.exit_code == 0
    assert result.stdout.splitlines()[0] == 'Started character creation: Boss'
    assert 'Pending:' in result.stdout
    assert 'Provide characteristics' in result.stdout


def test_cli_rejects_unknown_sophont(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'start', 'Boss', 'UnknownAlien', 'Troj', '2715'])

    assert result.exit_code != 0
    assert 'Unknown sophont: UnknownAlien' in result.output
    assert 'Available:' in result.output


def test_cli_reports_world_fetch_failure(tmp_path, monkeypatch):
    def fail_fetch_world(sector: str, hex_code: str):
        raise RuntimeError(f'{sector}/{hex_code} unavailable')

    monkeypatch.setattr('ceres.character.cli.fetch_world', fail_fetch_world)
    backend = SqliteCharacterBackend(':memory:')
    try:
        test_app = build_app(backend=backend, current_path=tmp_path / '.current')
        result = CliRunner().invoke(test_app, ['create', 'start', 'Boss', 'Vilani', 'Troj', '2715'])
    finally:
        backend.close()

    assert result.exit_code != 0
    assert 'Failed to fetch world Troj/2715: Troj/2715 unavailable' in result.output


def test_cli_lists_started_character_creations(memory_app):
    test_app = memory_app
    runner = CliRunner()

    _start_vilani(runner, test_app)
    runner.invoke(test_app, ['create', 'start', '-p', 'Anders', 'Lynn Rashid', 'Humaniti', 'Troj', '2715'])
    listed = runner.invoke(test_app, ['create', 'list'])

    assert listed.exit_code == 0
    assert listed.stdout.splitlines() == [
        '*  Id  Sophont   UCP     Player  Name',
        '   1   Vilani            NPC     Boss',
        '*  2   Humaniti          Anders  Lynn Rashid',
    ]


def test_cli_tracks_current_character_creation(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
    current_after_first = runner.invoke(memory_app, ['create', 'current'])
    runner.invoke(memory_app, ['create', 'start', '-p', 'Anders', 'Lynn Rashid', 'Humaniti', 'Troj', '2715'])
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


def test_cli_current_character_is_local_to_current_file(tmp_path, monkeypatch):
    monkeypatch.setattr('ceres.character.cli.fetch_world', lambda s, h: MOCK_WORLD)
    backend = SqliteCharacterBackend(':memory:')
    try:
        first_app = build_app(backend=backend, current_path=tmp_path / 'first' / '.current')
        second_app = build_app(backend=backend, current_path=tmp_path / 'second' / '.current')
        runner = CliRunner()

        _start_vilani(runner, first_app)
        runner.invoke(first_app, ['create', 'start', '-p', 'Anders', 'Lynn Rashid', 'Humaniti', 'Troj', '2715'])
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


def test_cli_rejects_stale_current_character_id(tmp_path):
    current_path = tmp_path / '.current'
    write_current_id(current_path, 999)
    backend = SqliteCharacterBackend(':memory:')
    try:
        test_app = build_app(backend=backend, current_path=current_path)
        result = CliRunner().invoke(test_app, ['create', 'current'])
    finally:
        backend.close()

    assert result.exit_code != 0
    assert 'No current character creation' in result.output


def test_cli_shows_current_character_creation(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
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

    _start_vilani(runner, memory_app)
    runner.invoke(memory_app, ['create', 'start', '-p', 'Anders', 'Lynn Rashid', 'Humaniti', 'Troj', '2715'])
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

    _start_vilani(runner, memory_app)
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

    _start_vilani(runner, memory_app)
    changed = runner.invoke(memory_app, ['create', 'ucp', 'STR=7', 'DEX=8', 'END=6', 'INT=9', 'EDU=10', 'SOC=5'])
    shown = runner.invoke(memory_app, ['create', 'ucp'])

    assert changed.exit_code == 0
    assert changed.stdout.splitlines()[0] == 'STR 7 DEX 8 END 6 INT 9 EDU 10 SOC 5'
    assert 'background skill' in changed.stdout
    assert shown.exit_code == 0
    assert shown.stdout.splitlines() == ['STR 7 DEX 8 END 6 INT 9 EDU 10 SOC 5']


def test_cli_sets_current_ucp_from_short_form(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
    changed = runner.invoke(memory_app, ['create', 'ucp', '7788B4'])
    shown = runner.invoke(memory_app, ['create', 'ucp'])
    listed = runner.invoke(memory_app, ['create', 'list'])

    assert changed.exit_code == 0
    assert changed.stdout.splitlines()[0] == 'STR 7 DEX 7 END 8 INT 8 EDU 11 SOC 4'
    assert 'background skill' in changed.stdout
    assert shown.exit_code == 0
    assert shown.stdout.splitlines() == ['STR 7 DEX 7 END 8 INT 8 EDU 11 SOC 4']
    assert listed.exit_code == 0
    assert listed.stdout.splitlines() == [
        '*  Id  Sophont   UCP     Player  Name',
        '*  1   Vilani    7788B4  NPC     Boss',
    ]


def test_cli_lists_ucp_short_form(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
    runner.invoke(memory_app, ['create', 'ucp', 'STR=7', 'DEX=8', 'END=6', 'INT=9', 'EDU=10', 'SOC=5'])
    listed = runner.invoke(memory_app, ['create', 'list'])

    assert listed.exit_code == 0
    assert listed.stdout.splitlines() == [
        '*  Id  Sophont   UCP     Player  Name',
        '*  1   Vilani    7869A5  NPC     Boss',
    ]


def test_cli_patches_current_ucp_with_adjustments(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
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


def test_cli_rejects_ucp_with_stale_current_character_id(tmp_path):
    current_path = tmp_path / '.current'
    write_current_id(current_path, 999)
    backend = SqliteCharacterBackend(':memory:')
    try:
        test_app = build_app(backend=backend, current_path=current_path)
        result = CliRunner().invoke(test_app, ['create', 'ucp', '777777'])
    finally:
        backend.close()

    assert result.exit_code != 0
    assert 'No current character creation' in result.output


def test_cli_rejects_ucp_when_projection_is_unavailable(tmp_path):
    current_path = tmp_path / '.current'
    backend = ProjectionlessBackend(':memory:')
    try:
        character = backend.start(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')
        write_current_id(current_path, character['id'])
        test_app = build_app(backend=backend, current_path=current_path)
        result = CliRunner().invoke(test_app, ['create', 'ucp', '777777'])
    finally:
        backend.close()

    assert result.exit_code != 0
    assert 'No current character creation' in result.output


def test_cli_rejects_invalid_ucp_change(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
    result = runner.invoke(memory_app, ['create', 'ucp', 'FOO=7'])

    assert result.exit_code != 0
    assert 'Invalid UCP change: FOO=7' in result.output


def test_cli_reports_ucp_replay_error(tmp_path):
    current_path = tmp_path / '.current'
    backend = ReplayErrorBackend(':memory:')
    try:
        character = backend.start(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')
        write_current_id(current_path, character['id'])
        backend.fail_append = True
        test_app = build_app(backend=backend, current_path=current_path)
        result = CliRunner().invoke(test_app, ['create', 'ucp', '777777'])
    finally:
        backend.close()

    assert result.exit_code != 0
    assert 'synthetic replay failure' in result.output


def test_cli_renames_current_character_creation(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
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

    runner.invoke(memory_app, ['create', 'start', 'Boss', 'Vilani', 'Troj', '2715'])
    result = runner.invoke(memory_app, ['create', 'rename', ''])

    assert result.exit_code != 0
    assert 'Name must not be empty' in result.output


def test_cli_requires_character_name_when_starting_creation(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'start', '', 'Vilani', 'Troj', '2715'])

    assert result.exit_code != 0
    assert 'Name must not be empty' in result.output


def test_cli_deletes_current_character(memory_app):
    runner = CliRunner()

    runner.invoke(memory_app, ['create', 'start', 'Boss', 'Vilani', 'Troj', '2715'])
    runner.invoke(memory_app, ['create', 'start', 'Lynn', 'Vilani', 'Troj', '2715'])
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


def test_cli_rejects_status_without_current_character(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'status'])

    assert result.exit_code != 0
    assert 'No current character creation' in result.output


def test_cli_rejects_status_for_unknown_character(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'status', '999'])

    assert result.exit_code != 0
    assert 'Unknown character creation id: 999' in result.output


def test_cli_shows_status_for_current_character(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
    result = runner.invoke(memory_app, ['create', 'status'])

    assert result.exit_code == 0
    assert 'Boss  (Vilani)' in result.stdout
    assert 'Pending:' in result.stdout
    assert 'PendingUcp [blocking]' in result.stdout


def test_cli_rejects_event_without_current_character(memory_app):
    result = CliRunner().invoke(memory_app, ['create', 'event', '{"kind": "ucp", "ucp": "777777"}'])

    assert result.exit_code != 0
    assert 'No current character creation' in result.output


def test_cli_rejects_invalid_event_json(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
    result = runner.invoke(memory_app, ['create', 'event', '{not-json'])

    assert result.exit_code != 0
    assert 'Invalid JSON:' in result.output


def test_cli_rejects_invalid_event_payload(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
    result = runner.invoke(memory_app, ['create', 'event', '{"kind": "unknown"}'])

    assert result.exit_code != 0
    assert 'Invalid event:' in result.output


def test_cli_reports_event_replay_error(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
    result = runner.invoke(memory_app, ['create', 'event', '{"kind": "ucp_event", "ucp": "777777"}'])

    assert result.exit_code != 0
    assert 'Replay error:' in result.output


def test_cli_appends_event_and_shows_updated_status(memory_app):
    runner = CliRunner()

    _start_vilani(runner, memory_app)
    result = runner.invoke(memory_app, ['create', 'event', '{"kind": "ucp_event", "ucp": "777777", "fulfills": "1.0"}'])

    assert result.exit_code == 0
    assert 'UCP  777777' in result.stdout
    assert 'Pending:' in result.stdout


class TestRenderProjectionSummaryBenefits:
    """render_projection_summary should display non-characteristic benefits and cash."""

    def _projection(self, **kwargs) -> CharacterProjection:
        return CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
        )

    def test_benefits_shown_in_summary(self):
        projection = self._projection(benefits=[LAB_SHIP, SHIP_SHARE])
        lines = render_projection_summary(projection)
        combined = '\n'.join(lines)
        assert 'Lab Ship' in combined
        assert 'Ship Share' in combined

    def test_cash_shown_in_summary(self):
        projection = self._projection(cash=50000)
        lines = render_projection_summary(projection)
        combined = '\n'.join(lines)
        assert 'Cr50,000' in combined

    def test_zero_cash_not_shown(self):
        projection = self._projection(cash=0)
        lines = render_projection_summary(projection)
        combined = '\n'.join(lines)
        assert 'cash' not in combined.lower()
        assert 'Cr' not in combined

    def test_empty_benefits_not_shown(self):
        projection = self._projection(benefits=[])
        lines = render_projection_summary(projection)
        combined = '\n'.join(lines)
        assert 'Benefits' not in combined

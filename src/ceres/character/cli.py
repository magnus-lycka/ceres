import atexit
import json
from pathlib import Path
import re
from typing import Annotated

import typer

from ceres import settings
from ceres.character.characteristics import UCP_STATS
from ceres.character.events import AnyEvent, UcpEvent
from ceres.character.projection import CharacterProjection
from ceres.character.replay import ReplayError
from ceres.character.skills import SkillInfo, skill_list
from ceres.character.sophonts import SOPHONTS
from ceres.character.store import CharacterRow, SqliteCharacterBackend

_SPECIALITY_SKILLS: frozenset[str] = frozenset(s.type for s in skill_list() if s.specialities)

_UCP_CHANGE_PATTERN = re.compile(r'^([A-Z]{3})(?:(=)(\d+)|([+-])(\d+))$')
_UCP_SHORT_PATTERN = re.compile(r'^[0-9A-F]{6}$')


def _parse_ucp_change(change: str) -> tuple[str, str, int]:
    match = _UCP_CHANGE_PATTERN.match(change)
    if not match:
        raise ValueError(f'Invalid UCP change: {change}')
    stat = match.group(1)
    if stat not in UCP_STATS:
        raise ValueError(f'Invalid UCP change: {change}')
    if match.group(2) == '=':
        return stat, 'set', int(match.group(3))
    sign = 1 if match.group(4) == '+' else -1
    return stat, 'adjust', sign * int(match.group(5))


def _expand_ucp_changes(changes: list[str]) -> list[str]:
    expanded: list[str] = []
    for change in changes:
        if _UCP_SHORT_PATTERN.match(change):
            expanded.extend(f'{stat}={int(value, 16)}' for stat, value in zip(UCP_STATS, change, strict=True))
        else:
            expanded.append(change)
    return expanded


def read_current_id(current_path: Path) -> int | None:
    if not current_path.exists():
        return None
    value = current_path.read_text().strip()
    if not value:
        return None
    return int(value)


def write_current_id(current_path: Path, character_id: int) -> None:
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(f'{character_id}\n')


def render_character(character: CharacterRow) -> str:
    return f'{character["id"]} {character["sophont"]} {character["player"]} {character["name"]}'


def render_character_show(character: CharacterRow, projection: CharacterProjection | None) -> list[str]:
    lines = [
        f'Id: {character["id"]}',
        f'Sophont: {character["sophont"]}',
        f'Player: {character["player"]}',
        f'Name: {character["name"]}',
    ]
    if projection and projection.summary.characteristics:
        ucp_short = render_ucp_short(projection.summary.characteristics)
        if ucp_short:
            lines.append(f'UCP: {ucp_short}')
            lines.append(f'Characteristics: {render_ucp(projection.summary.characteristics)}')
    return lines


def render_ucp(ucp: dict[str, int]) -> str:
    if not ucp:
        return 'No UCP set'
    return ' '.join(f'{stat} {ucp[stat]}' for stat in UCP_STATS if stat in ucp)


def render_ucp_short(ucp: dict[str, int] | None) -> str:
    if not ucp:
        return ''
    if any(stat not in ucp for stat in UCP_STATS):
        return ''
    return ''.join(f'{ucp[stat]:X}' for stat in UCP_STATS)


def render_skill(skill: SkillInfo) -> str:
    if skill.specialities:
        return f'{skill.type}: {", ".join(skill.specialities)}'
    return skill.type


def render_projection_summary(projection: CharacterProjection) -> list[str]:
    s = projection.summary
    lines = []
    if s.name:
        career_part = ''
        if s.current_career:
            career_part = f'  |  {s.current_career}'
            if s.current_assignment:
                career_part += f' / {s.current_assignment}'
            if s.rank is not None:
                career_part += f'  rank {s.rank}'
            if s.term_count:
                career_part += f'  term {s.term_count}'
        lines.append(f'{s.name}  ({s.species or "?"}){career_part}')
    if s.characteristics:
        ucp_str = ''.join(f'{s.characteristics.get(stat, 0):X}' for stat in UCP_STATS)
        char_str = '  '.join(f'{stat} {s.characteristics.get(stat, 0)}' for stat in UCP_STATS)
        lines.append(f'UCP  {ucp_str}    {char_str}')
    if s.skills:
        skill_str = '  '.join(
            f'{k} (all)-{v}' if k in _SPECIALITY_SKILLS else f'{k} {v}' for k, v in sorted(s.skills.items())
        )
        lines.append(f'Skills  {skill_str}')
    if s.connections:
        conn_str = '  '.join(f'{c.kind}({c.source or "?"})' for c in s.connections)
        lines.append(f'Connections  {conn_str}')
    if s.problems:
        for prob in s.problems:
            lines.append(f'Problem  {prob}')
    return lines


def render_pending_inputs(projection: CharacterProjection) -> list[str]:
    if not projection.pending_inputs:
        return []
    lines = ['Pending:']
    for p in projection.pending_inputs:
        blocking = ' [blocking]' if p.blocking else ''
        lines.append(f'  {p.id}  {p.kind}{blocking}  — {p.instruction}')
    return lines


def build_app(backend: SqliteCharacterBackend | None = None, current_path: Path | None = None) -> typer.Typer:
    if backend is None:
        backend = SqliteCharacterBackend()
        atexit.register(backend.close)
    if current_path is None:
        current_path = settings.cache_dir() / 'current-character'
    app = typer.Typer()
    sophonts_app = typer.Typer()
    skills_app = typer.Typer()
    create_app = typer.Typer()
    app.add_typer(sophonts_app, name='sophonts')
    app.add_typer(skills_app, name='skills')
    app.add_typer(create_app, name='create')

    @sophonts_app.command('list')
    def list_sophonts_command() -> None:
        for sophont in SOPHONTS:
            typer.echo(sophont)

    @skills_app.command('list')
    def list_skills_command() -> None:
        for skill in skill_list():
            typer.echo(render_skill(skill))

    @create_app.command('start')
    def start_character_creation(
        name: str,
        sophont: str = typer.Option(..., '--sophont', '-s'),
        player: str = typer.Option('NPC', '--player', '-p'),
    ) -> None:
        if not name:
            typer.echo('Name must not be empty', err=True)
            raise typer.Exit(1)
        if sophont not in SOPHONTS:
            available = ', '.join(SOPHONTS)
            typer.echo(f'Unknown sophont: {sophont}', err=True)
            typer.echo(f'Available sophonts: {available}', err=True)
            raise typer.Exit(1)
        character = backend.start(sophont=sophont, player=player, name=name)
        write_current_id(current_path, character['id'])
        typer.echo(f'Started character creation: {name}')
        projection = backend.get_projection(character['id'])
        if projection:
            for line in render_pending_inputs(projection):
                typer.echo(line)

    @create_app.command('list')
    def list_character_creations() -> None:
        current_id = read_current_id(current_path)
        typer.echo('*  Id  Sophont   UCP     Player  Name')
        for character in backend.list_characters():
            marker = '*  ' if character['id'] == current_id else '   '
            projection = backend.get_projection(character['id'])
            ucp_short = render_ucp_short(projection.summary.characteristics if projection else None)
            typer.echo(
                f'{marker}{character["id"]:<3} {character["sophont"]:<9} {ucp_short:<7} '
                f'{character["player"]:<7} {character["name"]}'
            )

    @create_app.command('current')
    def current_character_creation() -> None:
        current_id = read_current_id(current_path)
        character = None if current_id is None else backend.get_character(current_id)
        if character is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        typer.echo(render_character(character))

    @create_app.command('show')
    def show_character_creation(character_id: Annotated[int | None, typer.Argument()] = None) -> None:
        if character_id is None:
            character_id = read_current_id(current_path)
            if character_id is None:
                typer.echo('No current character creation', err=True)
                raise typer.Exit(1)
        character = backend.get_character(character_id)
        if character is None:
            typer.echo(f'Unknown character creation id: {character_id}', err=True)
            raise typer.Exit(1)
        projection = backend.get_projection(character_id)
        for line in render_character_show(character, projection):
            typer.echo(line)

    @create_app.command('ucp')
    def ucp_command(
        changes: Annotated[list[str] | None, typer.Argument()] = None,
    ) -> None:
        current_id = read_current_id(current_path)
        if current_id is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        if backend.get_character(current_id) is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        projection = backend.get_projection(current_id)
        if projection is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        if not changes:
            typer.echo(render_ucp(projection.summary.characteristics))
            return
        current = dict(projection.summary.characteristics)
        try:
            for change in _expand_ucp_changes(changes):
                stat, operation, value = _parse_ucp_change(change)
                if operation == 'set':
                    current[stat] = value
                else:
                    current[stat] = current.get(stat, 0) + value
        except ValueError as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(1) from error
        new_ucp = ''.join(f'{current.get(stat, 0):X}' for stat in UCP_STATS)
        ucp_pending = next(
            (p for p in projection.pending_inputs if p.kind == 'ucp' and p.blocking),
            None,
        )
        try:
            backend.append_event(current_id, UcpEvent(ucp=new_ucp, fulfills=ucp_pending.id if ucp_pending else None))
        except ReplayError as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(1) from error
        typer.echo(render_ucp({stat: int(digit, 16) for stat, digit in zip(UCP_STATS, new_ucp, strict=True)}))
        updated = backend.get_projection(current_id)
        if updated:
            for line in render_pending_inputs(updated):
                typer.echo(line)

    @create_app.command('use')
    def use_character_creation(character_id: int) -> None:
        character = backend.get_character(character_id)
        if character is None:
            typer.echo(f'Unknown character creation id: {character_id}', err=True)
            raise typer.Exit(1)
        write_current_id(current_path, character_id)
        typer.echo(f'Current character creation: {character["name"]}')

    @create_app.command('delete')
    def delete_character_creation(character_id: int) -> None:
        deleted = backend.delete_character(character_id)
        if deleted is None:
            typer.echo(f'Unknown character creation id: {character_id}', err=True)
            raise typer.Exit(1)
        typer.echo(f'Deleted character creation: {deleted["name"]}')

    @create_app.command('rename')
    def rename_character_creation(name: str) -> None:
        if not name:
            typer.echo('Name must not be empty', err=True)
            raise typer.Exit(1)
        current_id = read_current_id(current_path)
        character = None if current_id is None else backend.rename_character(current_id, name)
        if character is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        typer.echo(f'Renamed character creation: {character["name"]}')

    @create_app.command('status')
    def status_command(character_id: Annotated[int | None, typer.Argument()] = None) -> None:
        if character_id is None:
            character_id = read_current_id(current_path)
            if character_id is None:
                typer.echo('No current character creation', err=True)
                raise typer.Exit(1)
        projection = backend.get_projection(character_id)
        if projection is None:
            typer.echo(f'Unknown character creation id: {character_id}', err=True)
            raise typer.Exit(1)
        for line in render_projection_summary(projection):
            typer.echo(line)
        for line in render_pending_inputs(projection):
            typer.echo(line)

    @create_app.command('event')
    def event_command(event_json: str) -> None:
        current_id = read_current_id(current_path)
        if current_id is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        try:
            raw = json.loads(event_json)
        except json.JSONDecodeError as exc:
            typer.echo(f'Invalid JSON: {exc}', err=True)
            raise typer.Exit(1) from exc
        from pydantic import TypeAdapter, ValidationError

        adapter: TypeAdapter[AnyEvent] = TypeAdapter(AnyEvent)
        try:
            event = adapter.validate_python(raw)
        except ValidationError as exc:
            typer.echo(f'Invalid event: {exc}', err=True)
            raise typer.Exit(1) from exc
        try:
            backend.append_event(current_id, event)
        except ReplayError as exc:
            typer.echo(f'Replay error: {exc}', err=True)
            raise typer.Exit(1) from exc
        projection = backend.get_projection(current_id)
        if projection:
            for line in render_projection_summary(projection):
                typer.echo(line)
            for line in render_pending_inputs(projection):
                typer.echo(line)

    return app


app = build_app()


if __name__ == '__main__':
    app()

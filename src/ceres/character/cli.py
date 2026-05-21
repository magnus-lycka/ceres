import atexit
import json
from pathlib import Path
from typing import Annotated

import typer

from ceres import settings
from ceres.character.characteristics import UCP_STATS
from ceres.character.projection import CharacterProjection
from ceres.character.replay import ReplayError
from ceres.character.skills import SkillInfo, skill_list
from ceres.character.sophonts import SOPHONTS
from ceres.character.store import CharacterRow, SqliteCharacterBackend


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


def render_character_show(character: CharacterRow, ucp: dict[str, int] | None) -> list[str]:
    lines = [
        f'Id: {character["id"]}',
        f'Sophont: {character["sophont"]}',
        f'Player: {character["player"]}',
        f'Name: {character["name"]}',
    ]
    ucp_short = render_ucp_short(ucp)
    if ucp_short:
        lines.append(f'UCP: {ucp_short}')
        lines.append(f'Characteristics: {render_ucp(ucp or {})}')
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
        skill_str = '  '.join(f'{k} {v}' for k, v in sorted(s.skills.items()))
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
            ucp_short = render_ucp_short(backend.get_ucp(character['id']))
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
        for line in render_character_show(character, backend.get_ucp(character_id)):
            typer.echo(line)

    @create_app.command('ucp')
    def ucp_command(
        changes: Annotated[list[str] | None, typer.Argument()] = None,
    ) -> None:
        current_id = read_current_id(current_path)
        if current_id is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        character = backend.get_character(current_id)
        if character is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        if not changes:
            ucp = backend.get_ucp(current_id)
            if ucp is None:
                typer.echo('No current character creation', err=True)
                raise typer.Exit(1)
            typer.echo(render_ucp(ucp))
            return
        try:
            ucp = backend.patch_ucp(current_id, changes)
        except ValueError as error:
            typer.echo(str(error), err=True)
            raise typer.Exit(1) from error
        if ucp is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        typer.echo(render_ucp(ucp))
        projection = backend.get_projection(current_id)
        if projection:
            for line in render_pending_inputs(projection):
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

        from ceres.character.events import AnyEvent

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

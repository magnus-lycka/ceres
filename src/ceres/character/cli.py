import atexit
from pathlib import Path

import typer

from ceres import settings
from ceres.character.sophonts import SOPHONTS
from ceres.character.store import SqliteCharacterBackend


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


def build_app(backend: SqliteCharacterBackend | None = None, current_path: Path | None = None) -> typer.Typer:
    if backend is None:
        backend = SqliteCharacterBackend()
        atexit.register(backend.close)
    if current_path is None:
        current_path = settings.cache_dir() / 'current-character'
    app = typer.Typer()
    sophonts_app = typer.Typer()
    create_app = typer.Typer()
    app.add_typer(sophonts_app, name='sophonts')
    app.add_typer(create_app, name='create')

    @sophonts_app.command('list')
    def list_sophonts_command() -> None:
        for sophont in SOPHONTS:
            typer.echo(sophont)

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

    @create_app.command('list')
    def list_character_creations() -> None:
        current_id = read_current_id(current_path)
        typer.echo('*  Id  Sophont   Player  Name')
        for character in backend.list_characters():
            marker = '*  ' if character['id'] == current_id else '   '
            typer.echo(
                f'{marker}{character["id"]:<3} {character["sophont"]:<9} {character["player"]:<7} {character["name"]}'
            )

    @create_app.command('current')
    def current_character_creation() -> None:
        current_id = read_current_id(current_path)
        character = None if current_id is None else backend.get_character(current_id)
        if character is None:
            typer.echo('No current character creation', err=True)
            raise typer.Exit(1)
        typer.echo(f'{character["id"]} {character["sophont"]} {character["player"]} {character["name"]}')

    @create_app.command('use')
    def use_character_creation(character_id: int) -> None:
        character = backend.get_character(character_id)
        if character is None:
            typer.echo(f'Unknown character creation id: {character_id}', err=True)
            raise typer.Exit(1)
        write_current_id(current_path, character_id)
        typer.echo(f'Current character creation: {character["name"]}')

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

    return app


app = build_app()


if __name__ == '__main__':
    app()

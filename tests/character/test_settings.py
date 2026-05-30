from typer.testing import CliRunner

from ceres import settings
from ceres.character.cli import build_app
from ceres.character.sophonts import VILANI
from ceres.character.store import SqliteCharacterBackend
from tests.character.helpers import MOCK_WORLD


def test_settings_directories_come_from_platformdirs(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'user_config_dir', lambda appname: str(tmp_path / appname / 'config'))
    monkeypatch.setattr(settings, 'user_data_dir', lambda appname: str(tmp_path / appname / 'data'))
    monkeypatch.setattr(settings, 'user_cache_dir', lambda appname: str(tmp_path / appname / 'cache'))

    assert settings.config_dir() == tmp_path / 'ceres' / 'config'
    assert settings.data_dir() == tmp_path / 'ceres' / 'data'
    assert settings.cache_dir() == tmp_path / 'ceres' / 'cache'


def test_sqlite_character_backend_defaults_to_ceres_data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'data_dir', lambda: tmp_path / 'data')

    with SqliteCharacterBackend() as backend:
        backend.start(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')

    assert (tmp_path / 'data' / 'characters.sqlite').exists()


def test_sqlite_character_backend_creates_database_parent_directory(tmp_path):
    database = tmp_path / 'missing' / 'characters.sqlite'

    with SqliteCharacterBackend(database) as backend:
        backend.start(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss')

    assert database.exists()


def test_cli_current_file_defaults_to_ceres_cache_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'cache_dir', lambda: tmp_path / 'cache')
    monkeypatch.setattr('ceres.character.cli.fetch_world', lambda s, h: MOCK_WORLD)
    backend = SqliteCharacterBackend(':memory:')
    try:
        cli = build_app(backend=backend)

        CliRunner().invoke(cli, ['create', 'start', 'Boss', 'Vilani', 'Troj', '2715'])

        assert (tmp_path / 'cache' / 'current-character').read_text() == '1\n'
    finally:
        backend.close()

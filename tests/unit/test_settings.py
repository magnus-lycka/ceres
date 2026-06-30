from pathlib import Path

from ceres import settings
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.store import SqliteCharacterBackend
from ceres.settings import cache_dir, config_dir, data_dir
from tests.unit.character.helpers import MOCK_WORLD, _creation_events, create_backend


def test_config_dir_returns_path():
    assert isinstance(config_dir(), Path)


def test_data_dir_returns_path():
    assert isinstance(data_dir(), Path)


def test_cache_dir_returns_path():
    assert isinstance(cache_dir(), Path)


def test_cache_dir_differs_from_data_dir():
    assert cache_dir() != data_dir()


def test_dirs_contain_ceres():
    assert 'ceres' in str(config_dir()).lower()
    assert 'ceres' in str(data_dir()).lower()
    assert 'ceres' in str(cache_dir()).lower()


def test_settings_directories_come_from_platformdirs(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'user_config_dir', lambda appname: str(tmp_path / appname / 'config'))
    monkeypatch.setattr(settings, 'user_data_dir', lambda appname: str(tmp_path / appname / 'data'))
    monkeypatch.setattr(settings, 'user_cache_dir', lambda appname: str(tmp_path / appname / 'cache'))

    assert settings.config_dir() == tmp_path / 'ceres' / 'config'
    assert settings.data_dir() == tmp_path / 'ceres' / 'data'
    assert settings.cache_dir() == tmp_path / 'ceres' / 'cache'


def test_sqlite_character_backend_defaults_to_ceres_data_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, 'data_dir', lambda: tmp_path / 'data')

    with create_backend() as backend:
        backend.start(_creation_events(VILANI, MOCK_WORLD, 'NPC', 'Boss'), player='NPC', name='Boss')

    assert (tmp_path / 'data' / 'characters.sqlite').exists()


def test_sqlite_character_backend_creates_database_parent_directory(tmp_path):
    database = tmp_path / 'missing' / 'characters.sqlite'

    with SqliteCharacterBackend(database) as backend:
        backend.start(_creation_events(VILANI, MOCK_WORLD, 'NPC', 'Boss'), player='NPC', name='Boss')

    assert database.exists()

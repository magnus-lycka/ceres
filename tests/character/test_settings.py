from ceres import settings
from ceres.character.mechanism.store import SqliteCharacterBackend
from ceres.character.sophonts import VILANI
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

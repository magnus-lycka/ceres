from fastapi.testclient import TestClient
import pytest

from ceres.character.app import build_app
from ceres.character.store import SqliteCharacterBackend
from ceres.worlds import SectorWorldFilters
from tests.worlds.test_sector_filters import _sample_worlds


@pytest.fixture
def client():
    with SqliteCharacterBackend(':memory:') as backend:
        yield TestClient(build_app(backend), follow_redirects=True)


def test_sector_filter_page_uses_sector_entries_without_full_world_fetch(client, monkeypatch):
    monkeypatch.setattr(
        'ceres.character.web.routes.SectorWorldFilters.from_travellermap',
        lambda sector_abbreviation: SectorWorldFilters(
            worlds=_sample_worlds(),
            sector_abbreviation=sector_abbreviation,
            sector_name='Trojan Reach',
            allegiance_names={'ImDd': 'Third Imperium, Domain of Deneb'},
        ),
    )

    r = client.get('/ui/worlds/sectors/Troj')
    assert r.status_code == 200
    assert 'Trojan Reach' in r.text
    assert '3 worlds' in r.text
    assert '3 matching worlds' in r.text
    assert 'ImDd' in r.text
    assert 'Third Imperium, Domain of Deneb' in r.text
    assert 'Ni' in r.text

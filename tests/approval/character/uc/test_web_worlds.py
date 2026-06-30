"""Approval snapshot for the world sector filter web page."""

from fastapi.testclient import TestClient
import pytest

from ceres.character.service import CharacterService
from ceres.character.web.app import build_app
from ceres.worlds import SectorWorldFilters
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.worlds.test_sector_filters import _sample_worlds


@pytest.fixture
def client():
    with CharacterService(':memory:') as service:
        yield TestClient(build_app(service), follow_redirects=True)


@pytest.mark.approval
def test_sector_filter_page(client, snapshot, monkeypatch):
    """Sector filter page renders worlds from SectorWorldFilters without a full world fetch."""
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
    snap = AnnotatedSnapshot({'status_code': r.status_code, 'body': r.text})
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

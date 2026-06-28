"""Approval snapshots for the character web UI."""

from fastapi.testclient import TestClient
import pytest

from ceres.character.domain.career import CITIZEN
from ceres.character.domain.character_start import PendingUcp
from ceres.character.domain.sophont import HUMANITI
from ceres.character.mechanism.store import SqliteCharacterBackend
from ceres.character.web.app import build_app
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD


@pytest.fixture
def client_with_backend():
    with SqliteCharacterBackend(':memory:') as backend:
        yield TestClient(build_app(backend), follow_redirects=True), backend


@pytest.mark.approval
def test_character_list(client_with_backend, monkeypatch, snapshot):
    """Character list page with a character showing UCP, current career, and rank."""
    from ceres.character.domain.career.career_data import CareerTerm
    from ceres.character.domain.character_state import CharacterSummary
    from ceres.character.domain.characteristics import Chars

    client, backend = client_with_backend
    backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Aria')
    citizen = CITIZEN
    assignment = citizen.assignment('Colonist')
    assert assignment is not None
    monkeypatch.setattr(
        backend,
        'get_summary',
        lambda character_id: CharacterSummary(
            name='Aria',
            sophont=HUMANITI,
            homeworld=MOCK_WORLD,
            characteristics={
                Chars.STR: 8,
                Chars.DEX: 9,
                Chars.END: 10,
                Chars.INT: 6,
                Chars.EDU: 7,
                Chars.SOC: 11,
            },
            rank=3,
            terms=[CareerTerm(career=citizen, assignment=assignment)],
        ),
    )
    r = client.get('/ui/')
    snap = AnnotatedSnapshot({'status_code': r.status_code, 'body': r.text})
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_wizard(client_with_backend, snapshot):
    """Wizard page for a freshly created character — UCP pending input form."""
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Clio')
    r = client.get(f'/ui/characters/{row["id"]}/wizard')
    snap = AnnotatedSnapshot({'status_code': r.status_code, 'body': r.text})
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_event_submission(client_with_backend, snapshot):
    """HTMX response after submitting UCP — shows next pending and OOB summary updates."""
    client, backend = client_with_backend
    row = backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Oryn')
    projection = backend.get_projection(row['id'])
    assert projection is not None
    pi = projection.pending_inputs[0]
    assert isinstance(pi, PendingUcp)
    r = client.post(
        f'/ui/characters/{row["id"]}/events',
        data={
            'kind': 'ucp',
            'fulfills': pi.id,
            'STR': '7',
            'DEX': '8',
            'END': '6',
            'INT': '9',
            'EDU': '10',
            'SOC': '5',
        },
    )
    snap = AnnotatedSnapshot({'status_code': r.status_code, 'body': r.text})
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

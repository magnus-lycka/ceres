from fastapi.testclient import TestClient
import pytest

from ceres.character.app import build_app
from ceres.character.store import SqliteCharacterBackend


@pytest.fixture
def memory_client():
    backend = SqliteCharacterBackend(':memory:')
    try:
        with TestClient(build_app(backend=backend)) as client:
            yield client
    finally:
        backend.close()


def test_api_lists_sophonts(memory_client):
    response = memory_client.get('/sophonts')

    assert response.status_code == 200
    assert response.json() == {'sophonts': ['Vilani', 'Humaniti']}


def test_api_creates_and_lists_characters(memory_client):
    first = memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    second = memory_client.post('/characters', json={'sophont': 'Humaniti', 'player': 'Anders', 'name': 'Lynn Rashid'})
    listed = memory_client.get('/characters')

    assert first.status_code == 200
    assert first.json() == {'id': 1, 'sophont': 'Vilani', 'player': 'NPC', 'name': 'Boss'}
    assert second.status_code == 200
    assert second.json() == {'id': 2, 'sophont': 'Humaniti', 'player': 'Anders', 'name': 'Lynn Rashid'}
    assert listed.status_code == 200
    assert listed.json() == {
        'characters': [
            {'id': 1, 'sophont': 'Vilani', 'player': 'NPC', 'name': 'Boss'},
            {'id': 2, 'sophont': 'Humaniti', 'player': 'Anders', 'name': 'Lynn Rashid'},
        ]
    }


def test_api_renames_character(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    renamed = memory_client.patch('/characters/1', json={'name': 'Flavius Rupert'})
    listed = memory_client.get('/characters')

    assert renamed.status_code == 200
    assert renamed.json() == {'id': 1, 'sophont': 'Vilani', 'player': 'NPC', 'name': 'Flavius Rupert'}
    assert listed.status_code == 200
    assert listed.json() == {
        'characters': [
            {'id': 1, 'sophont': 'Vilani', 'player': 'NPC', 'name': 'Flavius Rupert'},
        ]
    }


def test_api_rejects_rename_for_unknown_character(memory_client):
    renamed = memory_client.patch('/characters/999', json={'name': 'Flavius Rupert'})

    assert renamed.status_code == 404
    assert renamed.json() == {'detail': 'Unknown character creation id: 999'}


def test_api_rejects_empty_rename(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    renamed = memory_client.patch('/characters/1', json={'name': ''})

    assert renamed.status_code == 400
    assert renamed.json() == {'detail': 'Name must not be empty'}

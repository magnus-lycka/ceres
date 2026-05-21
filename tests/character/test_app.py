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


def test_api_lists_skills(memory_client):
    response = memory_client.get('/skills')

    assert response.status_code == 200
    skills = response.json()['skills']
    skill_names = [skill['name'] for skill in skills]
    assert 'Admin' in skill_names
    assert 'Animals' in skill_names
    assert 'Art' not in skill_names
    assert 'Creative Art' in skill_names
    assert 'Profession' not in skill_names
    assert 'Worker Profession' in skill_names
    assert 'Science' not in skill_names
    assert 'Space Science' in skill_names
    assert next(skill for skill in skills if skill['name'] == 'Space Science') == {
        'type': 'Space Science',
        'name': 'Space Science',
        'specialities': ['Astronomy', 'Cosmology', 'Planetology'],
    }


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


def test_api_gets_character_by_id(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.get('/characters/1')

    assert response.status_code == 200
    assert response.json() == {
        'id': 1,
        'sophont': 'Vilani',
        'player': 'NPC',
        'name': 'Boss',
        'ucp': {},
    }


def test_api_rejects_get_for_unknown_character(memory_client):
    response = memory_client.get('/characters/999')

    assert response.status_code == 404
    assert response.json() == {'detail': 'Unknown character creation id: 999'}


def test_api_gets_empty_ucp(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.get('/characters/1/ucp')

    assert response.status_code == 200
    assert response.json() == {'ucp': {}}


def test_api_patches_ucp_and_logs_note(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    first = memory_client.patch(
        '/characters/1/ucp',
        json={'changes': ['STR=7', 'DEX=8', 'END=6', 'INT=9', 'EDU=10', 'SOC=5']},
    )
    second = memory_client.patch('/characters/1/ucp', json={'changes': ['STR-2', 'DEX-1'], 'note': 'Aging'})
    shown = memory_client.get('/characters/1/ucp')
    character = memory_client.get('/characters/1')
    events = memory_client.get('/characters/1/events')

    assert first.status_code == 200
    assert first.json() == {'ucp': {'STR': 7, 'DEX': 8, 'END': 6, 'INT': 9, 'EDU': 10, 'SOC': 5}}
    assert second.status_code == 200
    assert second.json() == {'ucp': {'STR': 5, 'DEX': 7, 'END': 6, 'INT': 9, 'EDU': 10, 'SOC': 5}}
    assert shown.status_code == 200
    assert shown.json() == {'ucp': {'STR': 5, 'DEX': 7, 'END': 6, 'INT': 9, 'EDU': 10, 'SOC': 5}}
    assert character.status_code == 200
    assert character.json() == {
        'id': 1,
        'sophont': 'Vilani',
        'player': 'NPC',
        'name': 'Boss',
        'ucp': {'STR': 5, 'DEX': 7, 'END': 6, 'INT': 9, 'EDU': 10, 'SOC': 5},
    }
    assert events.status_code == 200
    assert events.json() == {
        'events': [
            {
                'kind': 'ucp_changed',
                'changes': ['STR=7', 'DEX=8', 'END=6', 'INT=9', 'EDU=10', 'SOC=5'],
                'note': None,
            },
            {'kind': 'ucp_changed', 'changes': ['STR-2', 'DEX-1'], 'note': 'Aging'},
        ]
    }


def test_api_patches_ucp_from_short_form(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.patch('/characters/1/ucp', json={'changes': ['7788B4']})

    assert response.status_code == 200
    assert response.json() == {'ucp': {'STR': 7, 'DEX': 7, 'END': 8, 'INT': 8, 'EDU': 11, 'SOC': 4}}


def test_api_rejects_invalid_ucp_change(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.patch('/characters/1/ucp', json={'changes': ['FOO=7']})

    assert response.status_code == 400
    assert response.json() == {'detail': 'Invalid UCP change: FOO=7'}


def test_api_rejects_ucp_patch_for_unknown_character(memory_client):
    response = memory_client.patch('/characters/999/ucp', json={'changes': ['STR=7']})

    assert response.status_code == 404
    assert response.json() == {'detail': 'Unknown character creation id: 999'}


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

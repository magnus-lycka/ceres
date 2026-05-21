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
    skill_types = [skill['type'] for skill in skills]
    assert 'Admin' in skill_types
    assert 'Animals' in skill_types
    assert 'Art' not in skill_types
    assert 'Creative Art' in skill_types
    assert 'Profession' not in skill_types
    assert 'Worker Profession' in skill_types
    assert 'Science' not in skill_types
    assert 'Space Science' in skill_types
    assert next(skill for skill in skills if skill['type'] == 'Space Science') == {
        'type': 'Space Science',
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


def test_api_patches_ucp_and_records_typed_events(memory_client):
    # Use EDU=0 ('786000') so no background_skills pending is created,
    # allowing a second UCP patch without fulfilling it.
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    first = memory_client.patch(
        '/characters/1/ucp',
        json={'changes': ['STR=7', 'DEX=8', 'END=6', 'INT=0', 'EDU=0', 'SOC=0']},
    )
    second = memory_client.patch('/characters/1/ucp', json={'changes': ['STR-2', 'DEX-1']})
    shown = memory_client.get('/characters/1/ucp')
    character = memory_client.get('/characters/1')
    events = memory_client.get('/characters/1/events')

    assert first.status_code == 200
    assert first.json() == {'ucp': {'STR': 7, 'DEX': 8, 'END': 6, 'INT': 0, 'EDU': 0, 'SOC': 0}}
    assert second.status_code == 200
    assert second.json() == {'ucp': {'STR': 5, 'DEX': 7, 'END': 6, 'INT': 0, 'EDU': 0, 'SOC': 0}}
    assert shown.status_code == 200
    assert shown.json() == {'ucp': {'STR': 5, 'DEX': 7, 'END': 6, 'INT': 0, 'EDU': 0, 'SOC': 0}}
    assert character.status_code == 200
    assert character.json() == {
        'id': 1,
        'sophont': 'Vilani',
        'player': 'NPC',
        'name': 'Boss',
        'ucp': {'STR': 5, 'DEX': 7, 'END': 6, 'INT': 0, 'EDU': 0, 'SOC': 0},
    }
    assert events.status_code == 200
    event_list = events.json()['events']
    assert event_list[0] == {
        'id': 1,
        'kind': 'character_started',
        'sophont': 'Vilani',
        'player': 'NPC',
        'name': 'Boss',
        'fulfills': None,
    }
    assert event_list[1] == {'id': 2, 'kind': 'ucp', 'ucp': '786000', 'fulfills': '1.0'}
    assert event_list[2] == {'id': 3, 'kind': 'ucp', 'ucp': '576000', 'fulfills': None}


def test_api_second_ucp_patch_rejected_while_background_skills_pending(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.patch('/characters/1/ucp', json={'changes': ['7869A5']})  # EDU=10 → 4 bg skills

    response = memory_client.patch('/characters/1/ucp', json={'changes': ['STR-1']})

    assert response.status_code == 400


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


def test_api_creation_produces_pending_input_for_ucp(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    projection = memory_client.get('/characters/1/projection')

    assert projection.status_code == 200
    data = projection.json()
    assert len(data['pending_inputs']) == 1
    assert data['pending_inputs'][0] == {
        'id': '1.0',
        'kind': 'ucp',
        'instruction': 'Provide characteristics (UCP)',
        'options': [],
        'blocking': True,
    }


def test_api_post_event_resolves_pending_ucp(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.post(
        '/characters/1/events',
        json={'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '1.0'},
    )

    assert response.status_code == 200
    data = response.json()
    # EDU=10 → DM+1 → 4 background skills pending after UCP is fulfilled
    assert len(data['pending_inputs']) == 1
    assert data['pending_inputs'][0]['kind'] == 'background_skills'
    assert data['pending_inputs'][0]['blocking'] is True
    assert data['summary']['characteristics'] == {
        'STR': 7,
        'DEX': 8,
        'END': 6,
        'INT': 9,
        'EDU': 10,
        'SOC': 5,
    }


def test_api_post_background_skills_resolves_pending(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post('/characters/1/events', json={'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '1.0'})

    response = memory_client.post(
        '/characters/1/events',
        json={
            'kind': 'background_skills',
            'skills': ['Admin', 'Athletics', 'Carouse', 'Drive'],
            'fulfills': '2.0',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data['pending_inputs']) == 1
    assert data['pending_inputs'][0]['kind'] == 'career'
    assert data['summary']['skills'] == {'Admin': 0, 'Athletics': 0, 'Carouse': 0, 'Drive': 0}


def test_api_post_background_skills_rejects_wrong_count(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post('/characters/1/events', json={'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '1.0'})

    response = memory_client.post(
        '/characters/1/events',
        json={'kind': 'background_skills', 'skills': ['Admin', 'Athletics'], 'fulfills': '2.0'},
    )

    assert response.status_code == 400


def test_api_post_background_skills_rejects_invalid_skill(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post('/characters/1/events', json={'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '1.0'})

    response = memory_client.post(
        '/characters/1/events',
        json={
            'kind': 'background_skills',
            'skills': ['Admin', 'FakeSkill', 'Carouse', 'Drive'],
            'fulfills': '2.0',
        },
    )

    assert response.status_code == 400


def test_api_post_event_rejects_unknown_fulfills(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.post(
        '/characters/1/events',
        json={'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '99.0'},
    )

    assert response.status_code == 400


def test_api_post_event_rejects_unrelated_event_while_blocking(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.post(
        '/characters/1/events',
        json={'kind': 'ucp', 'ucp': '7869A5'},
    )

    assert response.status_code == 400


def test_api_projection_404_for_unknown_character(memory_client):
    response = memory_client.get('/characters/999/projection')

    assert response.status_code == 404


def test_api_deletes_character(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post('/characters', json={'sophont': 'Humaniti', 'name': 'Lynn'})

    deleted = memory_client.delete('/characters/1')
    listed = memory_client.get('/characters')

    assert deleted.status_code == 200
    assert deleted.json() == {'id': 1, 'sophont': 'Vilani', 'player': 'NPC', 'name': 'Boss'}
    assert listed.json() == {'characters': [{'id': 2, 'sophont': 'Humaniti', 'player': 'NPC', 'name': 'Lynn'}]}


def test_api_delete_returns_404_for_unknown(memory_client):
    response = memory_client.delete('/characters/999')

    assert response.status_code == 404

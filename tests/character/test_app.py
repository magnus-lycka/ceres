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
    assert response.json() == {'id': 1, 'sophont': 'Vilani', 'player': 'NPC', 'name': 'Boss'}


def test_api_rejects_get_for_unknown_character(memory_client):
    response = memory_client.get('/characters/999')

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
            'skills': [{'type': 'Admin'}, {'type': 'Athletics'}, {'type': 'Carouse'}, {'type': 'Drive'}],
            'fulfills': '2.0',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data['pending_inputs']) == 1
    assert data['pending_inputs'][0]['kind'] == 'career'
    assert len(data['summary']['skills']) == 4
    assert {s['type'] for s in data['summary']['skills']} == {'Admin', 'Athletics', 'Carouse', 'Drive'}


def test_api_post_background_skills_rejects_wrong_count(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post('/characters/1/events', json={'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '1.0'})

    response = memory_client.post(
        '/characters/1/events',
        json={'kind': 'background_skills', 'skills': [{'type': 'Admin'}, {'type': 'Athletics'}], 'fulfills': '2.0'},
    )

    assert response.status_code == 400


def test_api_post_background_skills_rejects_invalid_skill(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post('/characters/1/events', json={'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '1.0'})

    response = memory_client.post(
        '/characters/1/events',
        json={
            'kind': 'background_skills',
            'skills': [{'type': 'Admin'}, {'type': 'FakeSkill'}, {'type': 'Carouse'}, {'type': 'Drive'}],
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


def test_api_events_records_typed_events(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post('/characters/1/events', json={'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '1.0'})

    events = memory_client.get('/characters/1/events')

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
    assert event_list[1] == {'id': 2, 'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '1.0'}


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


def _setup_through_background_skills(client) -> None:
    client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    client.post('/characters/1/events', json={'kind': 'ucp', 'ucp': '7869A5', 'fulfills': '1.0'})
    client.post(
        '/characters/1/events',
        json={
            'kind': 'background_skills',
            'skills': [{'type': 'Admin'}, {'type': 'Athletics'}, {'type': 'Carouse'}, {'type': 'Drive'}],
            'fulfills': '2.0',
        },
    )


def test_api_scholar_initial_training_creates_two_choice_pendings(memory_client):
    _setup_through_background_skills(memory_client)

    response = memory_client.post(
        '/characters/1/events',
        json={
            'kind': 'career',
            'career': 'Scholar',
            'assignment': 'Field Researcher',
            'qualification_roll': 5,
            'fulfills': '3.0',
        },
    )

    assert response.status_code == 200
    data = response.json()
    choice_pendings = [p for p in data['pending_inputs'] if p['kind'] == 'initial_training_choice']
    assert len(choice_pendings) == 2
    assert not any(p['kind'] == 'survive' for p in data['pending_inputs'])
    assert choice_pendings[0] == {
        'id': '4.0',
        'kind': 'initial_training_choice',
        'instruction': 'Initial training: choose one of Drive, Flyer',
        'options': ['Drive', 'Flyer'],
        'blocking': True,
    }
    _sciences = ['Life Science', 'Physical Science', 'Robotic Science', 'Social Science', 'Space Science']
    assert choice_pendings[1] == {
        'id': '4.1',
        'kind': 'initial_training_choice',
        'instruction': f'Initial training: choose one of {", ".join(_sciences)}',
        'options': _sciences,
        'blocking': True,
    }


def test_api_scholar_initial_training_choices_unlock_survive(memory_client):
    _setup_through_background_skills(memory_client)
    memory_client.post(
        '/characters/1/events',
        json={
            'kind': 'career',
            'career': 'Scholar',
            'assignment': 'Field Researcher',
            'qualification_roll': 5,
            'fulfills': '3.0',
        },
    )

    after_first = memory_client.post(
        '/characters/1/events',
        json={'kind': 'skill_choice', 'skill': {'type': 'Flyer'}, 'fulfills': '4.0'},
    )

    assert after_first.status_code == 200
    data = after_first.json()
    assert any(p['kind'] == 'initial_training_choice' for p in data['pending_inputs'])
    assert not any(p['kind'] == 'survive' for p in data['pending_inputs'])

    after_second = memory_client.post(
        '/characters/1/events',
        json={'kind': 'skill_choice', 'skill': {'type': 'Space Science'}, 'fulfills': '4.1'},
    )

    assert after_second.status_code == 200
    data = after_second.json()
    assert not any(p['kind'] == 'initial_training_choice' for p in data['pending_inputs'])
    assert any(p['kind'] == 'survive' for p in data['pending_inputs'])
    skill_types = {s['type'] for s in data['summary']['skills']}
    assert 'Flyer' in skill_types
    assert 'Space Science' in skill_types

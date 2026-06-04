from fastapi.testclient import TestClient
import pytest

from ceres.character.app import build_app
from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerEvent,
    CharacterStartedEvent,
    PendingBackgroundSkills,
    PendingCareerChoice,
    PendingInitialTrainingChoice,
    PendingSurvive,
    SkillChoiceEvent,
    UcpEvent,
)
from ceres.character.skills import (
    Admin,
    Animals,
    Athletics,
    Carouse,
    CreativeArt,
    Drive,
    Flyer,
    LifeScience,
    PhysicalScience,
    RoboticScience,
    SocialScience,
    SpaceScience,
    WorkerProfession,
)
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
    assert Admin.model_fields['type'].default in skill_types
    assert Animals.model_fields['type'].default in skill_types
    assert 'Art' not in skill_types
    assert CreativeArt.model_fields['type'].default in skill_types
    assert 'Profession' not in skill_types
    assert WorkerProfession.model_fields['type'].default in skill_types
    assert 'Science' not in skill_types
    _ss_type = SpaceScience.model_fields['type'].default
    assert _ss_type in skill_types
    assert next(skill for skill in skills if skill['type'] == _ss_type) == {
        'type': _ss_type,
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
    pending = data['pending_inputs'][0]
    assert pending['id'] == '1.0'
    assert pending['instruction'] == 'Provide characteristics (UCP)'
    assert pending['blocking'] is True
    assert pending['stat_names'] == ['STR', 'DEX', 'END', 'INT', 'EDU', 'SOC']


def test_api_post_event_resolves_pending_ucp(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.post(
        '/characters/1/events',
        json={'kind': UcpEvent.model_fields['kind'].default, 'ucp': '7869A5', 'fulfills': '1.0'},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data['pending_inputs']) == 1
    assert data['pending_inputs'][0]['kind'] == PendingBackgroundSkills.model_fields['kind'].default
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
    memory_client.post(
        '/characters/1/events',
        json={'kind': UcpEvent.model_fields['kind'].default, 'ucp': '7869A5', 'fulfills': '1.0'},
    )

    response = memory_client.post(
        '/characters/1/events',
        json={
            'kind': BackgroundSkillsEvent.model_fields['kind'].default,
            'skills': [
                {'type': Admin.model_fields['type'].default},
                {'type': Athletics.model_fields['type'].default},
                {'type': Carouse.model_fields['type'].default},
                {'type': Drive.model_fields['type'].default},
            ],
            'fulfills': '2.0',
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data['pending_inputs']) == 1
    assert data['pending_inputs'][0]['kind'] == PendingCareerChoice.model_fields['kind'].default
    assert len(data['summary']['skills']) == 4
    assert {s['type'] for s in data['summary']['skills']} == {
        Admin.model_fields['type'].default,
        Athletics.model_fields['type'].default,
        Carouse.model_fields['type'].default,
        Drive.model_fields['type'].default,
    }


def test_api_post_background_skills_rejects_wrong_count(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post(
        '/characters/1/events',
        json={'kind': UcpEvent.model_fields['kind'].default, 'ucp': '7869A5', 'fulfills': '1.0'},
    )

    response = memory_client.post(
        '/characters/1/events',
        json={
            'kind': BackgroundSkillsEvent.model_fields['kind'].default,
            'skills': [
                {'type': Admin.model_fields['type'].default},
                {'type': Athletics.model_fields['type'].default},
            ],
            'fulfills': '2.0',
        },
    )

    assert response.status_code == 400


def test_api_post_background_skills_rejects_invalid_skill(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post(
        '/characters/1/events',
        json={'kind': UcpEvent.model_fields['kind'].default, 'ucp': '7869A5', 'fulfills': '1.0'},
    )

    response = memory_client.post(
        '/characters/1/events',
        json={
            'kind': BackgroundSkillsEvent.model_fields['kind'].default,
            'skills': [
                {'type': Admin.model_fields['type'].default},
                {'type': 'FakeSkill'},
                {'type': Carouse.model_fields['type'].default},
                {'type': Drive.model_fields['type'].default},
            ],
            'fulfills': '2.0',
        },
    )

    assert response.status_code == 400


def test_api_post_event_rejects_unknown_fulfills(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.post(
        '/characters/1/events',
        json={'kind': UcpEvent.model_fields['kind'].default, 'ucp': '7869A5', 'fulfills': '99.0'},
    )

    assert response.status_code == 400


def test_api_post_event_rejects_unrelated_event_while_blocking(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})

    response = memory_client.post(
        '/characters/1/events',
        json={'kind': UcpEvent.model_fields['kind'].default, 'ucp': '7869A5'},
    )

    assert response.status_code == 400


def test_api_projection_404_for_unknown_character(memory_client):
    response = memory_client.get('/characters/999/projection')

    assert response.status_code == 404


def test_api_events_records_typed_events(memory_client):
    memory_client.post('/characters', json={'sophont': 'Vilani', 'name': 'Boss'})
    memory_client.post(
        '/characters/1/events',
        json={'kind': UcpEvent.model_fields['kind'].default, 'ucp': '7869A5', 'fulfills': '1.0'},
    )

    events = memory_client.get('/characters/1/events')

    assert events.status_code == 200
    event_list = events.json()['events']
    e0 = event_list[0]
    assert e0['id'] == 1
    assert e0['kind'] == CharacterStartedEvent.model_fields['kind'].default
    assert e0['sophont'] == 'Vilani'
    assert e0['player'] == 'NPC'
    assert e0['name'] == 'Boss'
    assert e0['fulfills'] is None
    assert e0['homeworld']['name'] == 'Terra'
    assert event_list[1] == {
        'id': 2,
        'kind': UcpEvent.model_fields['kind'].default,
        'ucp': '7869A5',
        'fulfills': '1.0',
    }


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
    client.post(
        '/characters/1/events',
        json={'kind': UcpEvent.model_fields['kind'].default, 'ucp': '7869A5', 'fulfills': '1.0'},
    )
    client.post(
        '/characters/1/events',
        json={
            'kind': BackgroundSkillsEvent.model_fields['kind'].default,
            'skills': [
                {'type': Admin.model_fields['type'].default},
                {'type': Athletics.model_fields['type'].default},
                {'type': Carouse.model_fields['type'].default},
                {'type': Drive.model_fields['type'].default},
            ],
            'fulfills': '2.0',
        },
    )


def test_api_scholar_initial_training_creates_one_choice_pending(memory_client):
    # Character has Drive from background skills; Drive/Flyer row yields only Flyer
    # which is auto-granted (single-option → no dialog). Science row yields 5 choices.
    _setup_through_background_skills(memory_client)

    response = memory_client.post(
        '/characters/1/events',
        json={
            'kind': CareerEvent.model_fields['kind'].default,
            'career': 'Scholar',
            'assignment': 'Field Researcher',
            'qualification_roll': 5,
            'fulfills': '3.0',
        },
    )

    assert response.status_code == 200
    data = response.json()
    _it_kind = PendingInitialTrainingChoice.model_fields['kind'].default
    _survive_kind = PendingSurvive.model_fields['kind'].default
    choice_pendings = [p for p in data['pending_inputs'] if p['kind'] == _it_kind]
    assert len(choice_pendings) == 1
    assert not any(p['kind'] == _survive_kind for p in data['pending_inputs'])
    _science_display_names = sorted(
        ['Life Science', 'Physical Science', 'Robotic Science', 'Social Science', 'Space Science']
    )
    _science_types = {
        LifeScience.model_fields['type'].default,
        PhysicalScience.model_fields['type'].default,
        RoboticScience.model_fields['type'].default,
        SocialScience.model_fields['type'].default,
        SpaceScience.model_fields['type'].default,
    }
    assert choice_pendings[0]['id'] == '4.0'
    assert choice_pendings[0]['kind'] == _it_kind
    assert choice_pendings[0]['instruction'] == f'Initial training: choose one of {", ".join(_science_display_names)}'
    assert {o['type'] for o in choice_pendings[0]['options']} == _science_types


def test_api_scholar_initial_training_choices_unlock_survive(memory_client):
    # Flyer is auto-granted (Drive already known, only one option left → no dialog).
    # Only the Science choice requires user input.
    _setup_through_background_skills(memory_client)
    memory_client.post(
        '/characters/1/events',
        json={
            'kind': CareerEvent.model_fields['kind'].default,
            'career': 'Scholar',
            'assignment': 'Field Researcher',
            'qualification_roll': 5,
            'fulfills': '3.0',
        },
    )

    after_science = memory_client.post(
        '/characters/1/events',
        json={
            'kind': SkillChoiceEvent.model_fields['kind'].default,
            'skill': {'type': SpaceScience.model_fields['type'].default},
            'fulfills': '4.0',
        },
    )

    assert after_science.status_code == 200
    data = after_science.json()
    _it_kind = PendingInitialTrainingChoice.model_fields['kind'].default
    _survive_kind = PendingSurvive.model_fields['kind'].default
    assert not any(p['kind'] == _it_kind for p in data['pending_inputs'])
    assert any(p['kind'] == _survive_kind for p in data['pending_inputs'])
    skill_types = {s['type'] for s in data['summary']['skills']}
    assert Flyer.model_fields['type'].default in skill_types
    assert SpaceScience.model_fields['type'].default in skill_types

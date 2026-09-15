"""Character HTTP contracts: exercise the interface used by Svelte."""

import json
import sqlite3

from fastapi.testclient import TestClient
import httpx2
import pytest

from ceres.character.domain.career.career_events import MishapHandler
from ceres.character.service import CharacterService
from ceres.character.web.app import build_app


@pytest.fixture
def client():
    with CharacterService(':memory:') as service, TestClient(build_app(service)) as http:
        yield http


def test_unreplayable_character_can_be_listed_and_deleted_without_blocking_others(tmp_path):
    database = tmp_path / 'characters.sqlite'
    with CharacterService(database) as service:
        broken_id = service.create_character('Old character', 'NPC')
        good_id = service.create_character('Ada', 'Magnus')
    # A saved log whose pending references no longer match the current domain.
    with sqlite3.connect(database) as connection:
        payload = {'id': 2, 'fulfills': [999, 0], 'handler': MishapHandler(roll=4).model_dump(mode='json')}
        connection.execute(
            'insert into events (character_id, id, fulfills_event_id, fulfills_seq, payload) values (?, 2, 999, 0, ?)',
            (broken_id, json.dumps(payload)),
        )
    with CharacterService(database) as service, TestClient(build_app(service)) as http:
        response = http.get('/api/characters')
        assert response.status_code == 200
        assert response.json() == [
            {'id': broken_id, 'name': 'Old character', 'player': 'NPC', 'sophont': ''},
            {'id': good_id, 'name': 'Ada', 'player': 'Magnus', 'sophont': ''},
        ]
        assert http.get(f'/api/characters/{good_id}').json()['name'] == 'Ada'
        failed = http.get(f'/api/characters/{broken_id}')
        assert failed.status_code == 409
        assert 'cannot be replayed' in failed.json()['detail']
        assert http.delete(f'/api/characters/{broken_id}').status_code == 204
        assert [item['id'] for item in http.get('/api/characters').json()] == [good_id]


def test_create_list_and_resume_with_declarative_homeworld_choice(client):
    response = client.post('/api/characters', json={'name': 'Ada', 'player': 'NPC'})
    assert response.status_code == 201
    view = response.json()
    assert view['name'] == 'Ada'
    assert view['finished'] is False
    assert view['term_status'] == 'Starting term 1'
    assert view['age_display'] == '18'
    assert view['rank_display'] is None
    assert view['pending']['inputs'][0]['kind'] == 'SelectWorld'
    assert view['pending']['id']
    assert client.get(f'/api/characters/{view["id"]}').json() == view
    assert client.get('/api/characters').json()[0]['name'] == 'Ada'


def test_creation_history_reports_a_mishap_once(tmp_path):
    from ceres.character.domain.career import MERCHANT
    from ceres.character.domain.career.career_events import (
        CareerEntryHandler,
        PendingMishap,
        PendingSurvive,
        SurviveHandler,
    )
    from ceres.character.domain.character_start import BackgroundSkillsHandler, UcpHandler
    from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive
    from ceres.character.domain.sophont import VILANI
    from ceres.character.mechanism.event_base import Event
    from tests.unit.character.helpers import MOCK_WORLD, _creation_events, create_backend

    database = tmp_path / 'history.sqlite'
    events = _creation_events(VILANI, MOCK_WORLD)
    ucp = Event(fulfills=(events[-1].id, 0), handler=UcpHandler(ucp='7869A5'))
    background = Event(
        fulfills=(ucp.id, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
    )
    entry = Event(
        fulfills=(background.id, 0),
        handler=CareerEntryHandler(
            career=MERCHANT,
            assignment=MERCHANT.assignment('Merchant Marine'),
            qualification_roll=7,
        ),
    )
    backend = create_backend(database)
    row = backend.start([*events, ucp, background, entry], name='Test', player='NPC')
    with CharacterService(database) as service, TestClient(build_app(service)) as http:
        assert http.get(f'/api/characters/{row["id"]}').json()['rank_display'] == 'Rank 0'
    for pending_type, handler in [(PendingSurvive, SurviveHandler(roll=2)), (PendingMishap, MishapHandler(roll=3))]:
        projection = backend.get_projection(row['id'])
        assert projection is not None
        pending = next(p for p in projection.pending_inputs if isinstance(p, pending_type))
        backend.append_event(row['id'], Event(fulfills=pending.pending_id, handler=handler))
    backend.close()
    with CharacterService(database) as service, TestClient(build_app(service)) as http:
        view = http.get(f'/api/characters/{row["id"]}').json()
        mishaps = [entry for entry in view['history'] if 'A sudden war destroys your trade routes' in entry]
        assert len(mishaps) == 1
        assert mishaps[0].startswith('Term 1 mishap (Merchant): ')
        assert view['term_status'] == 'Ending term 1'
        assert view['age_display'] == '22'


@pytest.mark.parametrize('reenlist', ['true', 'false'])
def test_university_and_following_career_share_lifetime_terms_and_age_ranges(client, reenlist):
    from tests.unit.character.helpers import MOCK_WORLD

    view = client.post('/api/characters', json={'name': 'Student'}).json()
    url = f'/api/characters/{view["id"]}'

    def choose(values):
        nonlocal view
        response = client.post(url + '/choices', json={'fulfills': view['pending']['id'], 'values': values})
        assert response.status_code == 200, response.text
        view = response.json()

    def basic_choice():
        values = {}
        for spec in view['pending']['inputs']:
            if spec['kind'] == 'NumberEntry':
                values[spec['name']] = str(min(7, spec['max']))
            elif spec['kind'] == 'Select':
                selected = [option[1] for option in spec['options'][: spec['min_select']]]
                values[spec['name']] = selected if spec['max_select'] > 1 else selected[0]
            elif spec['kind'] == 'Reference':
                values[spec['name']] = spec['value']
            elif spec['kind'] == 'TextEntry':
                values[spec['name']] = spec['value'] or 'Test contact'
        assert values, view['pending']
        choose(values)

    def career_choice_available():
        return any(spec['kind'] == 'CareerChoice' for spec in view['pending']['inputs'])

    choose({'sector': MOCK_WORLD.sector_abbreviation, 'hex_code': MOCK_WORLD.hex})
    choose({'sophont': 'Humaniti'})
    for _ in range(10):
        if career_choice_available():
            break
        basic_choice()
    assert career_choice_available()
    choose({'kind': 'precareer_entry', 'precareer': 'University', 'roll': '9'})
    assert (view['term_status'], view['age_display']) == ('In term 1', '18–22')
    saw_ending = False
    for _ in range(20):
        if career_choice_available():
            break
        if view['term_status'] == 'Ending term 1':
            assert view['age_display'] == '22'
            saw_ending = True
        basic_choice()
    assert saw_ending
    assert (view['term_status'], view['age_display']) == ('Starting term 2', '22')
    choose({'career': 'Merchant', 'assignment': 'Merchant Marine', 'roll': '9'})
    assert (view['term_status'], view['age_display']) == ('In term 2', '22–26')
    for _ in range(12):
        if any(entry.startswith('Term 2 event (Merchant):') for entry in view['history']):
            break
        basic_choice()
    assert any(entry.startswith('Term 1 event (University):') for entry in view['history'])
    assert any(entry.startswith('Term 2 event (Merchant):') for entry in view['history'])
    for _ in range(15):
        if view['pending']['instruction'] == 'Reenlist or muster out?':
            break
        basic_choice()
    assert view['pending']['inputs'] == [
        {
            'kind': 'ActionChoice',
            'name': 'reenlist',
            'options': [['Reenlist', 'true'], ['Muster out', 'false']],
        }
    ]
    choose({'reenlist': reenlist})
    if reenlist == 'true':
        assert (view['term_status'], view['age_display']) == ('In term 3', '26–30')
    else:
        assert view['pending']['instruction'].startswith('Muster out:')


@pytest.mark.parametrize(('dexterity', 'dm', 'needed'), [(1, '-2', 8), (9, '+1', 5), (15, '+3', 3)])
def test_survival_and_advancement_show_modifiers_and_accept_raw_rolls(client, dexterity, dm, needed):
    from tests.unit.character.helpers import MOCK_WORLD

    view = client.post('/api/characters', json={'name': 'Rogue'}).json()
    url = f'/api/characters/{view["id"]}'

    def choose(values):
        nonlocal view
        response = client.post(url + '/choices', json={'fulfills': view['pending']['id'], 'values': values})
        assert response.status_code == 200, response.text
        view = response.json()

    choose({'sector': MOCK_WORLD.sector_abbreviation, 'hex_code': MOCK_WORLD.hex})
    choose({'sophont': 'Humaniti'})
    saw_survival = False
    for _ in range(30):
        if view['pending']['instruction'].startswith('Advancement:'):
            break
        if view['pending']['instruction'].startswith('Survive:'):
            saw_survival = True
            assert {
                'kind': 'InfoText',
                'text': f'Roll {needed}+ on 2D to survive. DEX DM {dm} is applied automatically. '
                'A natural 2 always fails.',
            } in view['pending']['inputs']
            choose({'roll': str(needed)})
            continue
        values: dict[str, str | list[str]] = {}
        for spec in view['pending']['inputs']:
            if spec['kind'] == 'CareerChoice':
                values = {'career': 'Rogue', 'assignment': 'Pirate', 'roll': '9'}
            elif spec['kind'] == 'NumberEntry':
                values[spec['name']] = '9' if spec['name'] == 'INT' else str(min(6, spec['max']))
                if spec['name'] == 'DEX':
                    values[spec['name']] = str(dexterity)
            elif spec['kind'] == 'Select':
                selected = [option[1] for option in spec['options'][: spec['min_select']]]
                values[spec['name']] = selected if spec['max_select'] > 1 else selected[0]
            elif spec['kind'] == 'Reference':
                values[spec['name']] = spec['value']
            elif spec['kind'] == 'TextEntry':
                values[spec['name']] = spec['value'] or 'Fellow rogue'
        assert values, view['pending']
        choose(values)
    assert view['pending']['instruction'].startswith('Advancement:')
    assert saw_survival
    inputs = view['pending']['inputs']
    assert {'kind': 'InfoText', 'text': 'Applied automatically: INT DM +1; event DM +2; total DM +3.'} in inputs
    roll = next(spec for spec in inputs if spec['kind'] == 'NumberEntry')
    assert roll['label'] == '2D roll (2–12, before DMs)'
    choose({'roll': '3'})
    assert view['rank_display'].startswith('Rank 1')


@pytest.mark.parametrize(('education', 'roll', 'succeeds'), [(6, 8, True), (10, 7, True), (10, 6, False)])
def test_advanced_training_roll_then_select_existing_skill(client, education, roll, succeeds):
    from tests.unit.character.helpers import MOCK_WORLD

    view = client.post('/api/characters', json={'name': 'Student'}).json()
    url = f'/api/characters/{view["id"]}'

    def choose(values):
        nonlocal view
        response = client.post(url + '/choices', json={'fulfills': view['pending']['id'], 'values': values})
        assert response.status_code == 200, response.text
        view = response.json()

    choose({'sector': MOCK_WORLD.sector_abbreviation, 'hex_code': MOCK_WORLD.hex})
    choose({'sophont': 'Humaniti'})
    choose({'STR': '7', 'DEX': '8', 'END': '6', 'INT': '9', 'EDU': str(education), 'SOC': '5'})
    skills = view['pending']['inputs'][0]
    choose({skills['name']: [option[1] for option in skills['options'][: skills['min_select']]]})
    choose({'career': 'Merchant', 'assignment': 'Merchant Marine', 'roll': '9'})
    choose({'roll': '7'})
    choose({'roll': '9'})
    assert not any(spec['kind'] == 'Select' for spec in view['pending']['inputs'])
    number = next(spec for spec in view['pending']['inputs'] if spec['kind'] == 'NumberEntry')
    assert number['label'] == 'EDU check: 2D roll (2–12, before DMs)'
    previous_skills = view['skills']
    choose({'roll': str(roll)})
    if succeeds:
        choice = view['pending']['inputs'][0]
        assert choice['kind'] == 'Select', view['pending']
        admin = next(value for label, value in choice['options'] if label == 'Admin')
        assert 'Admin 0' in previous_skills.replace('\N{NO-BREAK SPACE}', ' ')
        choose({choice['name']: admin})
        assert 'Admin 1' in view['skills'].replace('\N{NO-BREAK SPACE}', ' ')
    else:
        assert view['skills'] == previous_skills
    assert view['pending']['instruction'].startswith('Advancement:')


def test_required_relocation_supplies_a_world_picker_and_accepts_a_world(tmp_path, monkeypatch):
    from ceres.character.domain.character_start import CharacterCreatedHandler
    from ceres.character.domain.homeworld.homeworld_events import HomeworldChangeRequiredHandler
    from ceres.character.mechanism.event_base import Event
    from ceres.character.mechanism.store import SqliteCharacterBackend
    from tests.unit.character.helpers import MOCK_WORLD

    monkeypatch.setattr(
        'ceres.character.domain.homeworld.homeworld_events.fetch_world',
        lambda sector, hex_code: MOCK_WORLD.model_copy(update={'bases': 'S'}),
    )
    database = tmp_path / 'relocation.sqlite'
    backend = SqliteCharacterBackend(database)
    row = backend.start(
        [
            Event(id=1, handler=CharacterCreatedHandler(name='Ada', player='NPC')),
            Event(
                fulfills=(1, 0),
                handler=HomeworldChangeRequiredHandler(
                    reason='Choose a Scout base world', target_constraints='world_with_scout_base'
                ),
            ),
        ],
        name='Ada',
        player='NPC',
    )
    backend.close()
    with CharacterService(database) as service, TestClient(build_app(service)) as http:
        url = f'/api/characters/{row["id"]}'
        view = http.get(url).json()
        picker = next(spec for spec in view['pending']['inputs'] if spec['kind'] == 'SelectWorld')
        assert picker['filters']['bases'] == ['S', 'W']
        response = http.post(
            url + '/choices',
            json={
                'fulfills': view['pending']['id'],
                'values': {'sector': MOCK_WORLD.sector_abbreviation, 'hex_code': MOCK_WORLD.hex},
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()['homeworld'] == MOCK_WORLD.name


def test_optional_relocation_offers_change_or_skip_and_preserves_homeworld_on_skip(tmp_path):
    from ceres.character.domain.character_start import CharacterCreatedHandler, HomeworldSelectedHandler
    from ceres.character.domain.homeworld.homeworld_events import HomeworldChangeOfferedHandler
    from ceres.character.mechanism.event_base import Event
    from tests.unit.character.helpers import MOCK_WORLD, create_backend

    database = tmp_path / 'optional-homeworld.sqlite'
    backend = create_backend(database)
    row = backend.start(
        [
            Event(id=1, handler=CharacterCreatedHandler(name='Ada', player='NPC')),
            Event(id=2, fulfills=(1, 0), handler=HomeworldSelectedHandler(homeworld=MOCK_WORLD)),
            Event(
                fulfills=(2, 0),
                handler=HomeworldChangeOfferedHandler(
                    reason='Optional relocation', target_constraints='world_with_scout_base'
                ),
            ),
        ],
        name='Ada',
        player='NPC',
    )
    backend.close()
    with CharacterService(database) as service, TestClient(build_app(service)) as http:
        url = f'/api/characters/{row["id"]}'
        view = http.get(url).json()
        picker = next(spec for spec in view['pending']['inputs'] if spec['kind'] == 'SelectWorld')
        assert picker['open_label'] == 'Change Homeworld'
        assert picker['skip_values'] == {'keep': '1'}
        assert picker['reference_world'] == {
            'sector_abbreviation': MOCK_WORLD.sector_abbreviation,
            'hex': MOCK_WORLD.hex,
        }
        assert picker['filters']['bases'] == ['S', 'W']
        response = http.post(
            url + '/choices', json={'fulfills': view['pending']['id'], 'values': picker['skip_values']}
        )
        assert response.status_code == 200
        assert response.json()['homeworld'] == MOCK_WORLD.name
        assert response.json()['pending'] is None


@pytest.mark.parametrize('path', ['/api/sectors?q=Spin', '/api/worlds/Spin'])
def test_travellermap_network_failure_returns_retryable_service_error(client, monkeypatch, path):
    from ceres.character.web import world_api
    from ceres.worlds import SectorWorldFilters

    def unavailable(*args, **kwargs):
        raise httpx2.ConnectError('TravellerMap unavailable')

    monkeypatch.setattr(world_api, 'search_sectors', unavailable)
    monkeypatch.setattr(SectorWorldFilters, 'from_travellermap', unavailable)
    response = client.get(path)
    assert response.status_code == 503
    assert response.json()['detail'] == 'TravellerMap unavailable. Please retry.'


def test_submit_choice_undo_and_missing_character_are_http_results(client):
    from tests.unit.character.helpers import MOCK_WORLD

    view = client.post('/api/characters', json={'name': 'Ada'}).json()
    url = f'/api/characters/{view["id"]}'
    response = client.post(
        url + '/choices',
        json={
            'fulfills': view['pending']['id'],
            'values': {'sector': MOCK_WORLD.sector_abbreviation, 'hex_code': MOCK_WORLD.hex},
        },
    )
    assert response.status_code == 200
    following = response.json()
    assert following['homeworld'] == MOCK_WORLD.name
    assert following['pending']['inputs'][0]['kind'] == 'Select'
    assert following['changes']
    stale = client.post(url + '/choices', json={'fulfills': view['pending']['id'], 'values': {}})
    assert stale.status_code == 409
    assert client.post(url + '/undo').json()['pending'] == view['pending']
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404
    assert client.get('/api/characters').json() == []


def test_world_filters_and_pdf_remain_available(client, monkeypatch):
    from ceres.adapters.travellermap import SectorWorldEntry
    from ceres.worlds import SectorWorldFilters

    extra = {
        'ix': '',
        'ex': '',
        'cx': '',
        'nobility': '',
        'bases': '',
        'zone': '',
        'pbg': '000',
        'world_count': '1',
        'stellar': 'G2 V',
    }
    sector = SectorWorldFilters(
        worlds=[
            SectorWorldEntry(hex='0101', name='Garden', uwp='A867A99-C', remarks='Ga', allegiance='Im', **extra),
            SectorWorldEntry(hex='0102', name='Rock', uwp='D100000-0', remarks='Va', allegiance='Na', **extra),
        ],
        sector_abbreviation='Test',
        sector_name='Test sector',
    )
    monkeypatch.setattr(SectorWorldFilters, 'from_travellermap', lambda _: sector)
    response = client.get('/api/worlds/Test', params={'remarks': 'Ga'})
    assert response.status_code == 200
    assert [world['name'] for world in response.json()['worlds']] == ['Garden']
    assert response.json()['worlds'][0]['sector_abbreviation'] == 'Test'
    assert response.json()['worlds'][0]['distance'] is None
    assert 'Va' in response.json()['options']['remarks']
    assert client.get('/api/characters/999/pdf').status_code == 404


def test_reference_search_crosses_sector_borders_and_sorts_filtered_worlds(client, monkeypatch):
    from ceres.adapters import travellermap
    from tests.unit.character.helpers import MOCK_WORLD

    def nearby(sector, hex_code, radius):
        assert (sector, hex_code, radius) == ('Core', '0202', 12)
        return [
            MOCK_WORLD.model_copy(
                update={'name': 'Far', 'sector': 'Core', 'sector_abbreviation': 'Core', 'hex': '0205', 'bases': 'W'}
            ),
            MOCK_WORLD.model_copy(
                update={
                    'name': 'Across border',
                    'sector': 'Dagudashaag',
                    'sector_abbreviation': 'Dagu',
                    'hex': '3202',
                    'bases': 'S',
                }
            ),
            MOCK_WORLD.model_copy(
                update={'name': 'Near', 'sector': 'Core', 'sector_abbreviation': 'Core', 'hex': '0203', 'bases': 'S'}
            ),
            MOCK_WORLD.model_copy(
                update={
                    'name': 'No Scout base',
                    'sector': 'Core',
                    'sector_abbreviation': 'Core',
                    'hex': '0202',
                    'bases': 'N',
                }
            ),
        ]

    monkeypatch.setattr(travellermap, 'fetch_jump_worlds', nearby)
    monkeypatch.setattr(
        travellermap, 'fetch_sector_coordinates', lambda sector: {'Core': (0, 0), 'Dagu': (-1, 0)}[sector]
    )
    response = client.get('/api/worlds/Core', params={'reference_hex': '0202', 'bases': ['S', 'W']})
    assert response.status_code == 200
    worlds = response.json()['worlds']
    assert [(world['name'], world['sector_abbreviation'], world['distance']) for world in worlds] == [
        ('Near', 'Core', 1),
        ('Across border', 'Dagu', 2),
        ('Far', 'Core', 3),
    ]


def test_first_step_cannot_be_undone_and_api_serves_the_svelte_app(tmp_path):
    (tmp_path / '200.html').write_text('<main>Ceres application</main>')
    (tmp_path / 'app.js').write_text('/* application */')
    with CharacterService(':memory:') as service:
        client = TestClient(build_app(service, web_directory=tmp_path))
        view = client.post('/api/characters', json={'name': 'Ada'}).json()
        assert client.post(f'/api/characters/{view["id"]}/undo').status_code == 409
        assert client.get(f'/api/characters/{view["id"]}').json()['name'] == 'Ada'
        assert 'Ceres application' in client.get('/characters?id=1').text
        assert client.get('/app.js').text == '/* application */'
        assert client.get('/api/missing').status_code == 404


def test_numeric_bounds_are_enforced_without_losing_the_choice(client):
    from tests.unit.character.helpers import MOCK_WORLD

    view = client.post('/api/characters', json={'name': 'Ada'}).json()
    url = f'/api/characters/{view["id"]}'
    for values in ({'sector': MOCK_WORLD.sector_abbreviation, 'hex_code': MOCK_WORLD.hex}, {'sophont': 'Humaniti'}):
        response = client.post(url + '/choices', json={'fulfills': view['pending']['id'], 'values': values})
        assert response.status_code == 200
        view = response.json()
    values = {spec['name']: '7' for spec in view['pending']['inputs'] if spec['kind'] == 'NumberEntry'}
    values['STR'] = '999'
    response = client.post(url + '/choices', json={'fulfills': view['pending']['id'], 'values': values})
    assert response.status_code == 422
    assert client.get(url).json()['pending'] == view['pending']
    assert client.get(url + '/pdf').content.startswith(b'%PDF')

"""Unit tests for character web routes."""

from fastapi.testclient import TestClient
import pytest
from starlette.requests import Request

from ceres.character.domain.career.career_events import CareerEntryHandler, ReenlistHandler
from ceres.character.domain.character_start import UcpHandler
from ceres.character.mechanism.errors import ReplayError
from ceres.character.service import CharacterService
from ceres.character.web.app import build_app
from tests.unit.character.helpers import MOCK_WORLD

CAREER_CHOICE_PENDING_ID = (3, 0)
FILTERED_WORLD_PICKER_PENDING_ID = (3, 0)
REENLIST_PENDING_ID = (5, 1)
PROJECTION_CHARACTER_ID = 1
MISSING_CHARACTER_ID = 9999
URL_CHARACTER_ID = 7


@pytest.fixture
def service():
    with CharacterService(':memory:') as svc:
        yield svc


@pytest.fixture
def client(service):
    return TestClient(build_app(service), follow_redirects=False)


def _request(path: str) -> Request:
    raw_path, _, raw_query = path.partition('?')
    return Request(
        {
            'type': 'http',
            'method': 'GET',
            'path': raw_path,
            'query_string': raw_query.encode(),
            'headers': [],
            'server': ('testserver', 80),
            'scheme': 'http',
        }
    )


@pytest.fixture
def char_id(service):
    return service.create_character('Ada', 'NPC')


class TestCharacterListDoesNotReplay:
    def test_character_list_uses_stored_summary_not_replay(self, monkeypatch):
        with CharacterService(':memory:') as service:
            service.create_character('Stored', 'NPC')
            monkeypatch.setattr(
                service._backend,
                'get_projection',
                lambda character_id: pytest.fail('Character list must not replay event logs'),
            )
            client = TestClient(build_app(service), follow_redirects=True)
            r = client.get('/ui/')
        assert r.status_code == 200
        assert 'Stored' in r.text


class TestPendingUcpEventFromForm:
    def test_builds_ucp_string_from_characteristic_values(self):
        from ceres.character.domain.character_start import PendingUcp

        pi = PendingUcp(pending_id=(1, 0), instruction='')
        event = pi.event_from_form({'STR': '7', 'DEX': '8', 'END': '6', 'INT': '9', 'EDU': '10', 'SOC': '5'})
        assert isinstance(event.handler, UcpHandler)
        assert event.ucp == '7869A5'
        assert event.fulfills == pi.pending_id


class TestPendingCareerChoiceEventFromForm:
    def test_builds_career_entry_handler(self):
        from ceres.character.domain.career import SCOUT
        from ceres.character.domain.career.career_events import PendingCareerChoice

        pi = PendingCareerChoice(pending_id=CAREER_CHOICE_PENDING_ID, instruction='', options=[SCOUT])
        event = pi.event_from_form({'career': 'Scout', 'assignment': 'Courier', 'roll': '8'})
        assert isinstance(event.handler, CareerEntryHandler)
        assert event.career.name == 'Scout'
        assert event.assignment.name == 'Courier'
        assert event.qualification_roll == 8

    def test_unknown_assignment_raises(self):
        from ceres.character.domain.career import CITIZEN
        from ceres.character.domain.career.career_events import PendingCareerChoice

        pi = PendingCareerChoice(pending_id=CAREER_CHOICE_PENDING_ID, instruction='', options=[CITIZEN])
        with pytest.raises(ReplayError, match='Unknown assignment'):
            pi.event_from_form({'career': 'Citizen', 'assignment': '', 'roll': '8'})


class TestPendingReenlistEventFromForm:
    def test_reenlist_true(self):
        from ceres.character.domain.career.career_events import PendingReenlist

        pi = PendingReenlist(pending_id=REENLIST_PENDING_ID, instruction='')
        event = pi.event_from_form({'reenlist': 'true'})
        assert isinstance(event.handler, ReenlistHandler)
        assert event.reenlist is True

    def test_reenlist_false(self):
        from ceres.character.domain.career.career_events import PendingReenlist

        pi = PendingReenlist(pending_id=REENLIST_PENDING_ID, instruction='')
        event = pi.event_from_form({'reenlist': 'false'})
        assert isinstance(event.handler, ReenlistHandler)
        assert event.reenlist is False


class TestBuildEventFromForm:
    def test_unknown_pending_id_raises(self):
        from starlette.datastructures import FormData

        from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
        from ceres.character.domain.sophont import VILANI
        from ceres.character.web.routes import _build_event_from_form

        projection = CharacterProjection(
            character_id=PROJECTION_CHARACTER_ID,
            summary=CharacterSummary(name='T', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        with pytest.raises(ValueError):
            _build_event_from_form('nonexistent.0', FormData({}), projection)

    def test_string_pending_id_used_when_not_two_ints(self):
        from starlette.datastructures import FormData

        from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
        from ceres.character.domain.sophont import VILANI
        from ceres.character.web.routes import _build_event_from_form

        projection = CharacterProjection(
            character_id=PROJECTION_CHARACTER_ID,
            summary=CharacterSummary(name='T', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        with pytest.raises(ValueError):
            _build_event_from_form('not-two-ints', FormData({}), projection)


class TestNewCharacterForm:
    def test_get_returns_200(self, client):
        r = client.get('/ui/characters/new')
        assert r.status_code == 200

    def test_prefills_name_from_query(self, client):
        r = client.get('/ui/characters/new?name=Bob&player=Player1')
        assert r.status_code == 200
        assert 'Bob' in r.text


class TestCreateCharacter:
    def test_post_valid_redirects(self, client):
        r = client.post('/ui/characters/new', data={'name': 'Alice', 'player': 'NPC'})
        assert r.status_code == 303

    def test_post_empty_name_returns_422(self, client):
        r = client.post('/ui/characters/new', data={'name': '', 'player': 'NPC'})
        assert r.status_code == 422
        assert 'required' in r.text.lower() or 'Name' in r.text


class TestCharacterSheet:
    def test_returns_200_for_existing(self, client, char_id):
        r = client.get(f'/ui/characters/{char_id}')
        assert r.status_code == 200

    def test_returns_404_for_missing(self, client):
        r = client.get(f'/ui/characters/{MISSING_CHARACTER_ID}')
        assert r.status_code == 404


class TestCharacterWizard:
    def test_returns_200_for_existing(self, client, char_id):
        r = client.get(f'/ui/characters/{char_id}/wizard')
        assert r.status_code == 200

    def test_returns_404_for_missing(self, client):
        r = client.get(f'/ui/characters/{MISSING_CHARACTER_ID}/wizard')
        assert r.status_code == 404


class TestDeleteCharacter:
    def test_single_delete_redirects(self, client, char_id):
        r = client.post(f'/ui/characters/{char_id}/delete')
        assert r.status_code == 303

    def test_bulk_delete_redirects(self, client, char_id):
        r = client.post('/ui/characters/delete', data={'character_ids': str(char_id)})
        assert r.status_code == 303


class TestUndoLastEvent:
    def test_undo_redirects(self, client, char_id):
        r = client.post(f'/ui/characters/{char_id}/undo')
        assert r.status_code == 303


class TestPostEvent:
    def test_returns_html_for_missing_character(self, client):
        r = client.post(f'/ui/characters/{MISSING_CHARACTER_ID}/events')
        assert r.status_code == 404

    def test_returns_html_for_invalid_form(self, client, char_id, service):
        projection = service.get_projection(char_id)
        pending = projection.pending_inputs[0]
        r = client.post(f'/ui/characters/{char_id}/events', data={'fulfills': pending.id})
        assert r.status_code == 200

    def test_valid_homeworld_event_returns_200(self, client, char_id, service, monkeypatch):
        monkeypatch.setattr(
            'ceres.character.domain.homeworld.homeworld_events.fetch_world',
            lambda s, h: MOCK_WORLD,
        )
        projection = service.get_projection(char_id)
        pending = projection.pending_inputs[0]
        r = client.post(
            f'/ui/characters/{char_id}/events',
            data={
                'fulfills': pending.id,
                'sector': MOCK_WORLD.sector_abbreviation,
                'hex_code': MOCK_WORLD.hex,
            },
        )
        assert r.status_code == 200

    def test_replay_error_on_append_returns_200_with_error(self, client, char_id, service, monkeypatch):
        from ceres.character.mechanism.errors import ReplayError

        monkeypatch.setattr(
            'ceres.character.domain.homeworld.homeworld_events.fetch_world',
            lambda s, h: MOCK_WORLD,
        )
        projection = service.get_projection(char_id)
        pending = projection.pending_inputs[0]

        monkeypatch.setattr(service._backend, 'append_event', lambda cid, ev: (_ for _ in ()).throw(ReplayError('bad')))

        r = client.post(
            f'/ui/characters/{char_id}/events',
            data={
                'fulfills': pending.id,
                'sector': MOCK_WORLD.sector_abbreviation,
                'hex_code': MOCK_WORLD.hex,
            },
        )
        assert r.status_code == 200

    def test_projection_unavailable_after_append_returns_500(self, client, char_id, service, monkeypatch):
        monkeypatch.setattr(
            'ceres.character.domain.homeworld.homeworld_events.fetch_world',
            lambda s, h: MOCK_WORLD,
        )
        projection = service.get_projection(char_id)
        pending = projection.pending_inputs[0]
        calls = 0

        def get_projection_once_then_missing(cid):
            nonlocal calls
            calls += 1
            return projection if calls == 1 else None

        monkeypatch.setattr(service, 'get_projection', get_projection_once_then_missing)
        monkeypatch.setattr(service._backend, 'append_event', lambda cid, ev: None)

        r = client.post(
            f'/ui/characters/{char_id}/events',
            data={
                'fulfills': pending.id,
                'sector': MOCK_WORLD.sector_abbreviation,
                'hex_code': MOCK_WORLD.hex,
            },
        )

        assert r.status_code == 500
        assert 'Projection unavailable' in r.text


class TestSelectHomeworldForCharacter:
    def test_returns_404_for_missing_character(self, client):
        r = client.post(f'/ui/characters/{MISSING_CHARACTER_ID}/homeworld')
        assert r.status_code == 404

    def test_valid_submit_redirects(self, client, char_id, service, monkeypatch):
        monkeypatch.setattr(
            'ceres.character.domain.homeworld.homeworld_events.fetch_world',
            lambda s, h: MOCK_WORLD,
        )
        projection = service.get_projection(char_id)
        pending = projection.pending_inputs[0]
        r = client.post(
            f'/ui/characters/{char_id}/homeworld',
            data={
                'fulfills': pending.id,
                'sector': MOCK_WORLD.sector_abbreviation,
                'hex_code': MOCK_WORLD.hex,
            },
        )
        assert r.status_code == 303

    def test_stale_fulfills_redirects_to_wizard(self, client, char_id):
        r = client.post(
            f'/ui/characters/{char_id}/homeworld',
            data={'fulfills': '999.0', 'sector': 'Core', 'hex_code': '1202'},
        )
        assert r.status_code == 303
        assert r.headers['location'].endswith(f'/ui/characters/{char_id}/wizard')

    def test_exception_on_append_returns_422(self, client, char_id, service, monkeypatch):
        monkeypatch.setattr(
            'ceres.character.domain.homeworld.homeworld_events.fetch_world',
            lambda s, h: MOCK_WORLD,
        )
        projection = service.get_projection(char_id)
        pending = projection.pending_inputs[0]

        monkeypatch.setattr(service._backend, 'append_event', lambda cid, ev: (_ for _ in ()).throw(ValueError('oops')))

        r = client.post(
            f'/ui/characters/{char_id}/homeworld',
            data={
                'fulfills': pending.id,
                'sector': MOCK_WORLD.sector_abbreviation,
                'hex_code': MOCK_WORLD.hex,
            },
        )
        assert r.status_code == 422


class TestCharacterPdf:
    def test_returns_404_for_missing_character(self, client):
        r = client.get(f'/ui/characters/{MISSING_CHARACTER_ID}/pdf')
        assert r.status_code == 404

    def test_returns_pdf_for_existing_character(self, client, char_id, monkeypatch):
        monkeypatch.setattr('ceres.character.web.routes.render_stat_block_gallery_pdf', lambda specs, **kw: b'%PDF')
        r = client.get(f'/ui/characters/{char_id}/pdf')
        assert r.status_code == 200
        assert r.headers['content-type'] == 'application/pdf'


class TestGetCareerAssignments:
    def test_known_career_returns_assignments(self, client):
        r = client.get('/ui/careers/Scout/assignments')
        assert r.status_code == 200
        assert 'Courier' in r.text

    def test_unknown_career_returns_empty(self, client):
        r = client.get('/ui/careers/NotACareer/assignments')
        assert r.status_code == 200
        assert r.text == ''


class TestSectorPicker:
    def test_returns_200(self, client):
        r = client.get('/ui/worlds/sectors')
        assert r.status_code == 200

    def test_with_character_id_and_fulfills(self, client, char_id, service):
        projection = service.get_projection(char_id)
        pending = projection.pending_inputs[0]
        r = client.get(f'/ui/worlds/sectors?character_id={char_id}&fulfills={pending.id}')
        assert r.status_code == 200


class TestSectorSearch:
    def test_returns_200(self, client, monkeypatch):
        from ceres.adapters.travellermap import SectorInfo

        monkeypatch.setattr(
            'ceres.character.web.routes.search_sectors',
            lambda q: [
                SectorInfo(
                    x=0,
                    y=0,
                    milieu='M1105',
                    abbreviation='Spin',
                    tags='OTU',
                    names=['Spinward Marches'],
                )
            ],
        )

        r = client.get('/ui/worlds/sectors/search?q=spin')
        assert r.status_code == 200
        assert 'Spinward Marches' in r.text


class TestSectorFilters:
    def _mock_sector(self):
        from ceres.worlds import SectorWorldFilters

        return SectorWorldFilters(
            sector_abbreviation='Spin',
            sector_name='Spinward Marches',
            sector_x=0,
            sector_y=0,
        )

    def test_returns_200_with_mocked_travellermap(self, client, monkeypatch):
        mock = self._mock_sector()
        monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', lambda s: mock)
        r = client.get('/ui/worlds/sectors/Spin')
        assert r.status_code == 200

    def test_returns_503_on_network_error(self, client, monkeypatch):
        import httpx

        def _raise(s):
            raise httpx.TimeoutException('timeout')

        monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', _raise)
        r = client.get('/ui/worlds/sectors/Spin')
        assert r.status_code == 503

    def test_with_reference_hex_returns_distances(self, client, monkeypatch):
        mock = self._mock_sector()
        monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', lambda s: mock)
        r = client.get('/ui/worlds/sectors/Spin?reference_hex=0101')
        assert r.status_code == 200

    def test_combined_ref_extracts_sector_and_hex(self, client, monkeypatch):
        from ceres.adapters.travellermap import SectorInfo

        mock = self._mock_sector()
        monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', lambda s: mock)
        monkeypatch.setattr(
            'ceres.character.web.routes.search_sectors',
            lambda q: [
                SectorInfo(
                    x=-4,
                    y=1,
                    milieu='M1105',
                    abbreviation='Troj',
                    tags='OTU',
                    names=['Trojan Reach'],
                )
            ],
        )
        r = client.get('/ui/worlds/sectors/Spin?reference_hex=Troj2715')
        assert r.status_code == 200

    def test_combined_ref_keeps_existing_reference_sector(self, client, monkeypatch):
        mock = self._mock_sector()
        monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', lambda s: mock)
        r = client.get('/ui/worlds/sectors/Spin?reference_sector=Spin&reference_hex=Troj2715')
        assert r.status_code == 200

    def test_uses_character_homeworld_as_reference_hex(self, client, char_id, service, monkeypatch):
        from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
        from ceres.character.domain.sophont import VILANI

        mock = self._mock_sector()
        monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', lambda s: mock)
        projection = CharacterProjection(
            character_id=char_id,
            summary=CharacterSummary(name='Ada', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        monkeypatch.setattr(service, 'get_projection', lambda cid: projection)

        r = client.get(f'/ui/worlds/sectors/{MOCK_WORLD.sector_abbreviation}?character_id={char_id}')

        assert r.status_code == 200

    def test_unknown_reference_sector_disables_reference_hex(self, client, monkeypatch):
        mock = self._mock_sector()
        monkeypatch.setattr('ceres.character.web.routes.SectorWorldFilters.from_travellermap', lambda s: mock)
        monkeypatch.setattr('ceres.character.web.routes.search_sectors', lambda q: [])

        r = client.get('/ui/worlds/sectors/Spin?reference_sector=Unknown&reference_hex=0101')

        assert r.status_code == 200


class TestRouteHelpers:
    def test_world_picker_state_preserves_active_filters(self):
        from ceres.character.web.routes import _world_picker_state

        request = _request('/ui/worlds/sectors?name=Ada&filters=1&remarks=Ag&remarks=&tech_levels=A')

        assert _world_picker_state(request) == [
            ('name', 'Ada'),
            ('filters', '1'),
            ('remarks', 'Ag'),
            ('tech_levels', 'A'),
        ]

    def test_world_picker_query_can_exclude_filters(self):
        from ceres.character.web.routes import _world_picker_query

        request = _request('/ui/worlds/sectors?name=Ada&filters=1&remarks=Ag&tech_levels=A')

        assert _world_picker_query(request, include_filters=False) == 'name=Ada'

    def test_select_world_url_with_filter(self, client, char_id, service):
        from ceres.character.domain.character_start import PendingHomeworldSelection
        from ceres.character.input_specs import SelectWorld
        from ceres.character.web.routes import _select_world_url

        pending = PendingHomeworldSelection(pending_id=(1, 0), instruction='Pick homeworld')
        proj = service.get_projection(char_id)
        spec = pending.input_specs(proj)[0]
        assert isinstance(spec, SelectWorld)
        url = _select_world_url(spec, character_id=char_id, fulfills=pending.id)
        assert f'character_id={char_id}' in url

    def test_select_world_url_includes_sector_reference_and_filters(self):
        from ceres.character.domain.character_start import PendingHomeworldSelection
        from ceres.character.input_specs import SelectWorld, WorldFilterCriteria, WorldRef
        from ceres.character.web.routes import _select_world_url

        pending = PendingHomeworldSelection(
            pending_id=FILTERED_WORLD_PICKER_PENDING_ID,
            instruction='Pick homeworld',
        )
        spec = SelectWorld(
            name='homeworld',
            label='Homeworld',
            sector_abbreviation='Spin',
            reference_world=WorldRef(sector_abbreviation='Troj', hex='2715'),
            filters=WorldFilterCriteria(remarks=('Ag',), tech_levels=('A',)),
        )

        url = _select_world_url(
            spec,
            character_id=URL_CHARACTER_ID,
            fulfills=pending.id,
        )

        assert url.startswith('/ui/worlds/sectors/Spin?')
        assert 'reference_sector=Troj' in url
        assert 'reference_hex=2715' in url
        assert 'filters=1' in url
        assert 'remarks=Ag' in url
        assert 'tech_levels=A' in url

    def test_sector_coordinates_unknown_sector(self, monkeypatch):
        from ceres.character.web.routes import _sector_coordinates

        monkeypatch.setattr('ceres.character.web.routes.search_sectors', lambda q: [])

        assert _sector_coordinates('ZZZZZ') is None

    def test_sector_coordinates_finds_matching_abbreviation_case_insensitively(self, monkeypatch):
        from ceres.adapters.travellermap import SectorInfo
        from ceres.character.web.routes import _sector_coordinates

        monkeypatch.setattr(
            'ceres.character.web.routes.search_sectors',
            lambda q: [SectorInfo(x=-4, y=1, milieu='M1105', abbreviation='Troj', tags='OTU', names=['Trojan Reach'])],
        )

        assert _sector_coordinates('troj') == (-4, 1)

    def test_sector_coordinates_skips_non_matching_search_results(self, monkeypatch):
        from ceres.adapters.travellermap import SectorInfo
        from ceres.character.web.routes import _sector_coordinates

        monkeypatch.setattr(
            'ceres.character.web.routes.search_sectors',
            lambda q: [
                SectorInfo(x=0, y=0, milieu='M1105', abbreviation='Spin', tags='OTU', names=['Spinward Marches']),
                SectorInfo(x=-4, y=1, milieu='M1105', abbreviation='Troj', tags='OTU', names=['Trojan Reach']),
            ],
        )

        assert _sector_coordinates('troj') == (-4, 1)

    def test_sector_coordinates_empty_string(self):
        from ceres.character.web.routes import _sector_coordinates

        assert _sector_coordinates('') is None

    def test_selected_world_filters_default_to_empty_sets_when_filters_inactive(self):
        from ceres.character.web.routes import _selected_world_filters

        strings, ints, filters_active = _selected_world_filters(_request('/ui/worlds/sectors/Spin'))

        assert filters_active is False
        assert strings['allegiances'] == set()
        assert ints['tech_levels'] == set()

    def test_selected_world_filters_keep_only_submitted_groups_when_active(self):
        from ceres.character.web.routes import _selected_world_filters

        strings, ints, filters_active = _selected_world_filters(
            _request('/ui/worlds/sectors/Spin?filters=1&remarks=Ag&tech_levels=A')
        )

        assert filters_active is True
        assert strings == {'remarks': {'Ag'}}
        assert ints == {'tech_levels': {'A'}}

    def test_normalize_world_filters_removes_groups_where_all_options_are_selected(self):
        from ceres.adapters.travellermap import SectorWorldEntry
        from ceres.character.web.routes import _normalize_world_filters_for_matching
        from ceres.worlds import SectorWorldFilters

        def world(hex_code: str, name: str, uwp: str, remarks: str) -> SectorWorldEntry:
            return SectorWorldEntry(
                hex=hex_code,
                name=name,
                uwp=uwp,
                remarks=remarks,
                ix='',
                ex='',
                cx='',
                nobility='',
                bases='',
                zone='',
                pbg='',
                world_count='',
                allegiance='Im',
                stellar='',
            )

        sector = SectorWorldFilters(
            worlds=[
                world('0101', 'Alpha', 'A000000-A', 'Ag'),
                world('0102', 'Beta', 'B000000-B', 'Ri'),
            ]
        )

        strings, ints = _normalize_world_filters_for_matching(
            {'remarks': {'Ag', 'Ri'}},
            {'tech_levels': {'A', 'B'}},
            sector,
        )

        assert strings == {}
        assert ints == {}

    def test_term_detail_rows_include_precareer_and_career_terms(self):
        from ceres.character.domain.career import ARMY
        from ceres.character.domain.career.career_data import CareerTerm
        from ceres.character.domain.character_state import CharacterSummary
        from ceres.character.domain.precareer.loader import load_precareers
        from ceres.character.web.routes import _term_detail_rows

        university = next(precareer for precareer in load_precareers() if precareer.name == 'University')
        precareer_term = university.make_term()
        precareer_term.event = 'Met a professor'
        career_term = CareerTerm(career=ARMY, assignment=ARMY.assignment('Infantry'))
        career_term.mishap = 'Wounded'
        summary = CharacterSummary(name='Ada', terms=[precareer_term, career_term])

        rows = _term_detail_rows(summary)

        assert rows[0]['career'] == 'University'
        assert rows[0]['assignment'] == 'Pre-career'
        assert rows[0]['notes'] == [{'text': 'Met a professor', 'color': 'text-gray-500'}]
        assert rows[1]['career'] == 'Army'
        assert rows[1]['assignment'] == 'Infantry'
        assert rows[1]['notes'] == [{'text': 'Wounded', 'color': 'text-yellow-600/80'}]

"""Unit tests for character web routes."""

from fastapi.testclient import TestClient
import pytest

from ceres.character.domain.career.career_events import CareerEntryHandler, ReenlistHandler
from ceres.character.domain.character_start import UcpHandler
from ceres.character.mechanism.errors import ReplayError
from ceres.character.service import CharacterService
from ceres.character.web.app import build_app
from tests.unit.character.helpers import MOCK_WORLD


@pytest.fixture
def service():
    with CharacterService(':memory:') as svc:
        yield svc


@pytest.fixture
def client(service):
    return TestClient(build_app(service), follow_redirects=False)


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
        assert event.fulfills == (1, 0)


class TestPendingCareerChoiceEventFromForm:
    def test_builds_career_entry_handler(self):
        from ceres.character.domain.career import SCOUT
        from ceres.character.domain.career.career_events import PendingCareerChoice

        pi = PendingCareerChoice(pending_id=(3, 0), instruction='', options=[SCOUT])
        event = pi.event_from_form({'career': 'Scout', 'assignment': 'Courier', 'roll': '8'})
        assert isinstance(event.handler, CareerEntryHandler)
        assert event.career.name == 'Scout'
        assert event.assignment.name == 'Courier'
        assert event.qualification_roll == 8

    def test_unknown_assignment_raises(self):
        from ceres.character.domain.career import CITIZEN
        from ceres.character.domain.career.career_events import PendingCareerChoice

        pi = PendingCareerChoice(pending_id=(3, 0), instruction='', options=[CITIZEN])
        with pytest.raises(ReplayError, match='Unknown assignment'):
            pi.event_from_form({'career': 'Citizen', 'assignment': '', 'roll': '8'})


class TestPendingReenlistEventFromForm:
    def test_reenlist_true(self):
        from ceres.character.domain.career.career_events import PendingReenlist

        pi = PendingReenlist(pending_id=(5, 1), instruction='')
        event = pi.event_from_form({'reenlist': 'true'})
        assert isinstance(event.handler, ReenlistHandler)
        assert event.reenlist is True

    def test_reenlist_false(self):
        from ceres.character.domain.career.career_events import PendingReenlist

        pi = PendingReenlist(pending_id=(5, 1), instruction='')
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
            character_id=1,
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
            character_id=1,
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
        r = client.get('/ui/characters/9999')
        assert r.status_code == 404


class TestCharacterWizard:
    def test_returns_200_for_existing(self, client, char_id):
        r = client.get(f'/ui/characters/{char_id}/wizard')
        assert r.status_code == 200

    def test_returns_404_for_missing(self, client):
        r = client.get('/ui/characters/9999/wizard')
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
        r = client.post('/ui/characters/9999/events', data={'fulfills': '1.0'})
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


class TestSelectHomeworldForCharacter:
    def test_returns_404_for_missing_character(self, client):
        r = client.post('/ui/characters/9999/homeworld', data={'fulfills': '1.0', 'sector': 'Spin', 'hex_code': '0101'})
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
        r = client.get('/ui/characters/9999/pdf')
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


class TestRouteHelpers:
    def test_select_world_url_with_filter(self, client, char_id, service):
        from ceres.character.domain.character_start import PendingHomeworldSelection
        from ceres.character.input_specs import SelectWorld
        from ceres.character.web.routes import _select_world_url

        pending = PendingHomeworldSelection(pending_id=(1, 0), instruction='Pick homeworld')
        proj = service.get_projection(char_id)
        spec = pending.input_specs(proj)[0]
        assert isinstance(spec, SelectWorld)
        url = _select_world_url(spec, character_id=1, fulfills='1.0')
        assert 'character_id=1' in url

    def test_sector_coordinates_unknown_sector(self, monkeypatch):
        from ceres.character.web.routes import _sector_coordinates

        monkeypatch.setattr('ceres.character.web.routes.search_sectors', lambda q: [])

        assert _sector_coordinates('ZZZZZ') is None

    def test_sector_coordinates_empty_string(self):
        from ceres.character.web.routes import _sector_coordinates

        assert _sector_coordinates('') is None

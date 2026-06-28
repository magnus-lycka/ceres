"""Unit tests for character web routes."""

from fastapi.testclient import TestClient
import pytest

from ceres.character.domain.career.career_events import CareerEntryHandler, ReenlistHandler
from ceres.character.domain.character_start import UcpHandler
from ceres.character.domain.sophont import HUMANITI
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.store import SqliteCharacterBackend
from ceres.character.web.app import build_app
from tests.unit.character.helpers import MOCK_WORLD


class TestCharacterListDoesNotReplay:
    def test_character_list_uses_stored_summary_not_replay(self, monkeypatch):
        with SqliteCharacterBackend(':memory:') as backend:
            backend.start(sophont=HUMANITI, homeworld=MOCK_WORLD, player='NPC', name='Stored')
            monkeypatch.setattr(
                backend,
                'get_projection',
                lambda character_id: pytest.fail('Character list must not replay event logs'),
            )
            client = TestClient(build_app(backend), follow_redirects=True)
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

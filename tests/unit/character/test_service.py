"""Unit tests for CharacterService — the domain façade for character operations."""

import pytest

from ceres.character.domain.character_start import PendingHomeworldSelection, PendingSophontSelection, PendingUcp
from ceres.character.domain.sophont import HUMANITI
from ceres.character.service import CharacterService
from tests.unit.character.helpers import MOCK_WORLD


@pytest.fixture
def service():
    with CharacterService(':memory:') as svc:
        yield svc


class TestCreateCharacter:
    def test_returns_character_id(self, service):
        cid = service.create_character('Ada', 'NPC')
        assert isinstance(cid, int)
        assert cid > 0

    def test_sequential_ids_increase(self, service):
        first = service.create_character('Ada', 'NPC')
        second = service.create_character('Bob', 'NPC')
        assert second > first

    def test_character_appears_in_list(self, service):
        cid = service.create_character('Ada', 'NPC')
        items = service.list_characters()
        assert any(item.id == cid and item.name == 'Ada' for item in items)

    def test_first_pending_is_homeworld_selection(self, service):
        cid = service.create_character('Ada', 'NPC')
        projection = service.get_projection(cid)
        assert projection is not None
        assert len(projection.pending_inputs) >= 1
        assert isinstance(projection.pending_inputs[0], PendingHomeworldSelection)

    def test_homeworld_selection_is_blocking(self, service):
        cid = service.create_character('Ada', 'NPC')
        projection = service.get_projection(cid)
        assert projection is not None
        assert projection.pending_inputs[0].blocking is True


class TestListCharacters:
    def test_empty_when_no_characters(self, service):
        assert service.list_characters() == []

    def test_returns_all_characters(self, service):
        service.create_character('Ada', 'NPC')
        service.create_character('Bob', 'Player1')
        items = service.list_characters()
        assert len(items) == 2

    def test_list_item_has_name_player_and_id(self, service):
        cid = service.create_character('Ada', 'Player1')
        items = service.list_characters()
        item = next(i for i in items if i.id == cid)
        assert item.name == 'Ada'
        assert item.player == 'Player1'


class TestGetProjection:
    def test_returns_none_for_missing_character(self, service):
        assert service.get_projection(9999) is None

    def test_returns_projection_with_correct_name(self, service):
        cid = service.create_character('Ada', 'NPC')
        projection = service.get_projection(cid)
        assert projection is not None
        assert projection.summary.name == 'Ada'


class TestSubmitEvent:
    def test_submit_homeworld_creates_sophont_pending(self, service):
        cid = service.create_character('Ada', 'NPC')
        projection = service.get_projection(cid)
        assert projection is not None
        hw_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldSelection))
        service.submit_event(cid, hw_pending.id, {'sector': MOCK_WORLD.sector_abbreviation, 'hex_code': MOCK_WORLD.hex})
        projection = service.get_projection(cid)
        assert projection is not None
        assert any(isinstance(p, PendingSophontSelection) for p in projection.pending_inputs)

    def test_submit_full_creation_flow_reaches_ucp(self, service):
        cid = service.create_character('Ada', 'NPC')
        projection = service.get_projection(cid)
        assert projection is not None

        hw_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldSelection))
        service.submit_event(cid, hw_pending.id, {'sector': MOCK_WORLD.sector_abbreviation, 'hex_code': MOCK_WORLD.hex})

        projection = service.get_projection(cid)
        assert projection is not None
        soph_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingSophontSelection))
        service.submit_event(cid, soph_pending.id, {'sophont': HUMANITI.name})

        projection = service.get_projection(cid)
        assert projection is not None
        assert any(isinstance(p, PendingUcp) for p in projection.pending_inputs)

    def test_submit_unknown_pending_id_raises(self, service):
        cid = service.create_character('Ada', 'NPC')
        with pytest.raises(ValueError, match='pending'):
            service.submit_event(cid, '99.0', {'sector': 'Troj', 'hex': '3215'})

    def test_submit_invalid_form_data_raises(self, service):
        cid = service.create_character('Ada', 'NPC')
        projection = service.get_projection(cid)
        assert projection is not None
        hw_pending = next(p for p in projection.pending_inputs if isinstance(p, PendingHomeworldSelection))
        with pytest.raises(ValueError):
            service.submit_event(cid, hw_pending.id, {'sector': '', 'hex_code': ''})


class TestDeleteCharacter:
    def test_deleted_character_not_in_list(self, service):
        cid = service.create_character('Ada', 'NPC')
        service.delete_character(cid)
        assert not any(item.id == cid for item in service.list_characters())

    def test_deleted_character_projection_returns_none(self, service):
        cid = service.create_character('Ada', 'NPC')
        service.delete_character(cid)
        assert service.get_projection(cid) is None

    def test_delete_nonexistent_does_not_raise(self, service):
        service.delete_character(9999)


class TestRenameCharacter:
    def test_rename_updates_name_in_list(self, service):
        cid = service.create_character('Old Name', 'NPC')
        service.rename_character(cid, 'New Name')
        items = service.list_characters()
        item = next(i for i in items if i.id == cid)
        assert item.name == 'New Name'

    def test_rename_nonexistent_returns_false(self, service):
        result = service.rename_character(9999, 'Whatever')
        assert result is False

    def test_rename_returns_true_on_success(self, service):
        cid = service.create_character('Ada', 'NPC')
        result = service.rename_character(cid, 'New Name')
        assert result is True

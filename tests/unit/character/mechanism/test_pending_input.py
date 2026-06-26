"""Unit tests for pending_input.py — ChoiceBase, PendingInputBase, registry."""

import pytest

from ceres.character.mechanism.pending_input import ChoiceBase, PendingInputBase, _deserialise_pending_input


class TestPendingInputBaseRegistry:
    def test_registered_kinds_includes_survive(self):
        assert 'survive' in PendingInputBase._registry

    def test_registry_maps_kind_to_class(self):
        from ceres.character.domain.career.career_events import PendingSurvive

        assert PendingInputBase._registry['survive'] is PendingSurvive


class TestPendingInputBaseId:
    def test_tuple_pending_id_formats_as_dot_separated(self):
        from ceres.character.domain.career.career_events import PendingSurvive

        p = PendingSurvive(pending_id=(3, 1), instruction='Survive')
        assert p.id == '3.1'

    def test_string_pending_id_returns_as_is(self):
        from ceres.character.domain.characteristics import ConnectionKind
        from ceres.character.domain.connection_events import PendingConnectionName

        p = PendingConnectionName(
            pending_id='my_string_id',
            connection_index=0,
            connection_kind=ConnectionKind.ALLY,
            note_prefill='',
            instruction='Name your ally',
        )
        assert p.id == 'my_string_id'


class TestPendingInputBaseTemplateFragment:
    def test_returns_kind_string(self):
        from ceres.character.domain.career.career_events import PendingSurvive

        p = PendingSurvive(pending_id=(1, 0), instruction='Survive')
        assert p.template_fragment == 'survive'


class TestDeserialisePendingInput:
    def test_passes_through_existing_instance(self):
        from ceres.character.domain.career.career_events import PendingSurvive

        p = PendingSurvive(pending_id=(1, 0), instruction='Survive')
        result = _deserialise_pending_input(p)
        assert result is p

    def test_deserialises_dict_by_kind(self):
        from ceres.character.domain.career.career_events import PendingSurvive

        result = _deserialise_pending_input({'kind': 'survive', 'pending_id': [1, 0], 'instruction': 'Survive'})
        assert isinstance(result, PendingSurvive)

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match='Unknown pending input kind'):
            _deserialise_pending_input({'kind': 'nonexistent_kind', 'pending_id': [1, 0], 'instruction': 'X'})

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match='Cannot deserialise'):
            _deserialise_pending_input(42)


class TestChoiceBase:
    def test_handle_raises_not_implemented(self):
        from ceres.character.domain.career.career_events import SurviveHandler
        from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
        from ceres.character.domain.sophont import VILANI
        from ceres.character.mechanism.event_base import Event
        from tests.unit.character.helpers import MOCK_WORLD

        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='T', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        event = Event(handler=SurviveHandler(roll=5))
        base = ChoiceBase(kind='test', label='Test')
        with pytest.raises(NotImplementedError):
            base.handle(proj, event)

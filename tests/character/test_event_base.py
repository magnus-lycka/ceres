"""Tests for the event/pending handler base machinery.

Covers mechanism/event_base.py and mechanism/pending_input.py:
handler auto-registration, deserialization, Event proxying, PendingInput identity,
and the default method implementations on the base classes.
"""

from typing import Any, Literal

import pytest

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import (
    Event,
    EventHandlerBase,
    PendingHandlerBase,
    PendingInput,
    _deserialise_event_handler,
    _deserialise_pending_handler,
)
from ceres.character.mechanism.pending_input import PendingInputBase, _deserialise_pending_input
from tests.character.helpers import MOCK_WORLD

# ── Test-only handler stubs ──────────────────────────────────────────────────


class _AlphaHandler(EventHandlerBase):
    kind: Literal['_test_alpha'] = '_test_alpha'
    value: int = 0

    def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
        projection['applied'] = self.value


class _BetaHandler(EventHandlerBase):
    kind: Literal['_test_beta'] = '_test_beta'


class _HandlerWithoutKind(EventHandlerBase):
    pass


class _AlphaPendingHandler(PendingHandlerBase):
    kind: Literal['_test_pending_alpha'] = '_test_pending_alpha'
    label: str = ''


class _PendingWithoutKind(PendingHandlerBase):
    pass


# ── EventHandlerBase registration ────────────────────────────────────────────


class TestEventHandlerRegistration:
    def test_subclass_with_literal_kind_is_registered(self):
        assert EventHandlerBase._registry.get('_test_alpha') is _AlphaHandler

    def test_second_subclass_registered_under_its_own_kind(self):
        assert EventHandlerBase._registry.get('_test_beta') is _BetaHandler

    def test_subclass_without_kind_field_is_not_registered(self):
        assert _HandlerWithoutKind not in EventHandlerBase._registry.values()

    def test_event_and_pending_registries_are_independent(self):
        assert '_test_alpha' not in PendingHandlerBase._registry
        assert '_test_pending_alpha' not in EventHandlerBase._registry


# ── _deserialise_event_handler ───────────────────────────────────────────────


class TestDeserialiseEventHandler:
    def test_passes_through_existing_instance(self):
        h = _AlphaHandler(value=7)
        assert _deserialise_event_handler(h) is h

    def test_deserialises_dict_with_known_kind(self):
        result = _deserialise_event_handler({'kind': '_test_alpha', 'value': 3})
        assert isinstance(result, _AlphaHandler)
        assert result.value == 3

    def test_unknown_kind_raises_value_error(self):
        with pytest.raises(ValueError, match='Unknown event handler kind'):
            _deserialise_event_handler({'kind': 'does_not_exist'})

    def test_wrong_type_raises_value_error(self):
        with pytest.raises(ValueError, match='Cannot deserialise'):
            _deserialise_event_handler(42)

    def test_dict_missing_kind_key_raises_value_error(self):
        with pytest.raises(ValueError, match='Unknown event handler kind'):
            _deserialise_event_handler({'value': 5})


# ── Event ────────────────────────────────────────────────────────────────────


class TestEvent:
    def test_kind_property_delegates_to_handler(self):
        event = Event(handler=_AlphaHandler())
        assert event.kind == '_test_alpha'

    def test_id_is_auto_generated_when_not_specified(self):
        event_a = Event(handler=_AlphaHandler())
        event_b = Event(handler=_AlphaHandler())
        assert event_a.id != event_b.id

    def test_explicit_id_overrides_auto_generated(self):
        explicit_id = 42
        event = Event.model_validate({'id': explicit_id, 'handler': _AlphaHandler()})
        assert event.id == explicit_id

    def test_fulfills_defaults_to_none(self):
        event = Event(handler=_AlphaHandler())
        assert event.fulfills is None

    def test_fulfills_stored_correctly(self):
        pending_id = (3, 1)
        event = Event(fulfills=pending_id, handler=_AlphaHandler())
        assert event.fulfills == pending_id

    def test_apply_calls_handler_apply(self):
        projection: dict[str, Any] = {}
        event = Event(handler=_AlphaHandler(value=42))
        event.apply(projection)
        assert projection['applied'] == 42

    def test_apply_passes_fulfilled_pending(self):
        calls: list[Any] = []

        class _RecordHandler(EventHandlerBase):
            kind: Literal['_test_record'] = '_test_record'

            def apply(self, projection: Any, event: Event, fulfilled_pending: Any = None) -> None:
                calls.append(fulfilled_pending)

        event = Event(handler=_RecordHandler())
        sentinel = object()
        event.apply({}, fulfilled_pending=sentinel)
        assert calls == [sentinel]

    def test_getattr_proxies_handler_field(self):
        event = Event(handler=_AlphaHandler(value=99))
        assert event.value == 99  # type: ignore[attr-defined]

    def test_getattr_raises_for_missing_handler_attribute(self):
        event = Event(handler=_AlphaHandler())
        with pytest.raises(AttributeError):
            _ = event.no_such_attribute  # type: ignore[attr-defined]

    def test_getattr_does_not_shadow_event_own_id(self):
        explicit_id = 5
        event = Event.model_validate({'id': explicit_id, 'handler': _AlphaHandler(value=1)})
        assert event.id == explicit_id

    def test_handler_deserialised_from_dict_via_before_validator(self):
        event = Event.model_validate({'id': 1, 'handler': {'kind': '_test_alpha', 'value': 11}})
        assert isinstance(event.handler, _AlphaHandler)
        assert event.handler.value == 11


# ── EventHandlerBase.apply default ──────────────────────────────────────────


class TestEventHandlerBaseApply:
    def test_base_apply_raises_not_implemented(self):
        class _NoApply(EventHandlerBase):
            kind: Literal['_test_noapply'] = '_test_noapply'

        handler = _NoApply()
        with pytest.raises(NotImplementedError, match='apply\\(\\) not implemented'):
            handler.apply({}, Event(handler=handler))

    def test_base_init_replay_returns_none(self):
        handler = _BetaHandler()
        assert handler.init_replay(1, 1) is None


# ── PendingHandlerBase registration ─────────────────────────────────────────


class TestPendingHandlerRegistration:
    def test_subclass_with_literal_kind_is_registered(self):
        assert PendingHandlerBase._registry.get('_test_pending_alpha') is _AlphaPendingHandler

    def test_subclass_without_kind_is_not_registered(self):
        assert _PendingWithoutKind not in PendingHandlerBase._registry.values()


# ── PendingHandlerBase default methods ──────────────────────────────────────


class TestPendingHandlerBaseDefaults:
    def test_resolve_is_a_no_op(self):
        handler = _AlphaPendingHandler()
        handler.resolve({}, Event(handler=_AlphaHandler()))

    def test_input_specs_returns_empty_list(self):
        handler = _AlphaPendingHandler()
        assert handler.input_specs() == []

    def test_event_from_form_raises_not_implemented(self):
        handler = _AlphaPendingHandler()
        with pytest.raises(NotImplementedError, match='event_from_form\\(\\) not implemented'):
            handler.event_from_form({}, (0, 0))


# ── _deserialise_pending_handler ─────────────────────────────────────────────


class TestDeserialisePendingHandler:
    def test_passes_through_existing_instance(self):
        h = _AlphaPendingHandler(label='x')
        assert _deserialise_pending_handler(h) is h

    def test_deserialises_dict_with_known_kind(self):
        result = _deserialise_pending_handler({'kind': '_test_pending_alpha', 'label': 'hi'})
        assert isinstance(result, _AlphaPendingHandler)
        assert result.label == 'hi'

    def test_unknown_kind_raises_value_error(self):
        with pytest.raises(ValueError, match='Unknown pending handler kind'):
            _deserialise_pending_handler({'kind': 'no_such_pending'})

    def test_wrong_type_raises_value_error(self):
        with pytest.raises(ValueError, match='Cannot deserialise'):
            _deserialise_pending_handler('not_a_dict')


# ── PendingInput ─────────────────────────────────────────────────────────────


class TestPendingInput:
    def test_id_property_formats_as_event_dot_idx(self):
        pi = PendingInput(pending_id=(7, 2), handler=_AlphaPendingHandler())
        assert pi.id == '7.2'

    def test_blocking_defaults_to_true(self):
        pi = PendingInput(pending_id=(0, 0), handler=_AlphaPendingHandler())
        assert pi.blocking is True

    def test_blocking_can_be_set_false(self):
        pi = PendingInput(pending_id=(0, 0), blocking=False, handler=_AlphaPendingHandler())
        assert pi.blocking is False

    def test_handler_deserialised_from_dict(self):
        pi = PendingInput.model_validate(
            {'pending_id': (1, 0), 'handler': {'kind': '_test_pending_alpha', 'label': 'hello'}}
        )
        assert isinstance(pi.handler, _AlphaPendingHandler)
        assert pi.handler.label == 'hello'

    def test_pending_id_zero_zero_formats_correctly(self):
        pi = PendingInput(pending_id=(0, 0), handler=_AlphaPendingHandler())
        assert pi.id == '0.0'


# ── PendingInputBase registry (pending_input.py) ────────────────────────────


class _TestPendingAlpha(PendingInputBase):
    kind: Literal['_test_pending_input_alpha'] = '_test_pending_input_alpha'
    value: int = 0


class _TestPendingBeta(PendingInputBase):
    kind: Literal['_test_pending_input_beta'] = '_test_pending_input_beta'


class _TestPendingNoKind(PendingInputBase):
    pass


class TestPendingInputBaseRegistry:
    def test_subclass_with_literal_kind_is_registered(self):
        assert PendingInputBase._registry.get('_test_pending_input_alpha') is _TestPendingAlpha

    def test_second_subclass_registered_under_its_own_kind(self):
        assert PendingInputBase._registry.get('_test_pending_input_beta') is _TestPendingBeta

    def test_subclass_without_kind_is_not_registered(self):
        assert _TestPendingNoKind not in PendingInputBase._registry.values()

    def test_pending_input_base_registry_independent_of_event_handler_registry(self):
        assert '_test_pending_input_alpha' not in EventHandlerBase._registry


class TestDeserialisePendingInput:
    def test_passes_through_existing_instance(self):
        p = _TestPendingAlpha(pending_id=(1, 0), instruction='x', value=5)
        assert _deserialise_pending_input(p) is p

    def test_deserialises_dict_with_known_kind(self):
        result = _deserialise_pending_input(
            {'kind': '_test_pending_input_alpha', 'pending_id': [1, 0], 'instruction': 'hi', 'value': 7}
        )
        assert isinstance(result, _TestPendingAlpha)
        assert result.value == 7

    def test_unknown_kind_raises_value_error(self):
        with pytest.raises(ValueError, match='Unknown pending input kind'):
            _deserialise_pending_input({'kind': 'no_such_kind', 'pending_id': [0, 0], 'instruction': ''})

    def test_wrong_type_raises_value_error(self):
        with pytest.raises(ValueError, match='Cannot deserialise'):
            _deserialise_pending_input(99)


class TestCharacterProjectionPendingInputsRoundTrip:
    def _make_projection(self) -> CharacterProjection:
        from ceres.character.domain.career.career_events import PendingCareerChoice
        from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeRequired

        summary = CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD)
        proj = CharacterProjection(character_id=1, summary=summary)
        proj.pending_inputs.append(PendingCareerChoice(pending_id=(1, 0), instruction='Choose a career'))
        proj.pending_inputs.append(
            PendingHomeworldChangeRequired(pending_id=(1, 1), instruction='Choose homeworld', reason='test')
        )
        return proj

    def test_concrete_subclass_fields_survive_serialisation_round_trip(self):
        from ceres.character.domain.career.career_events import PendingCareerChoice

        proj = self._make_projection()
        data = proj.model_dump()
        restored = CharacterProjection.model_validate(data)
        assert isinstance(restored.pending_inputs[0], PendingCareerChoice)

    def test_all_pending_types_restored_to_correct_concrete_class(self):
        from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeRequired

        proj = self._make_projection()
        data = proj.model_dump()
        restored = CharacterProjection.model_validate(data)
        assert isinstance(restored.pending_inputs[1], PendingHomeworldChangeRequired)

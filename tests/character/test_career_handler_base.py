"""Tests for CareerHandlerBase: auto-registration, dispatch, and completeness."""

from typing import Literal, cast

import pytest

from ceres.character.careers.career_data import (
    CareerDispatchEffect,
    CareerHandlerBase,
    get_career_handler,
)


class TestCareerHandlerBaseClass:
    def test_career_handler_base_is_subclass_of_career_dispatch_effect(self):
        assert issubclass(CareerHandlerBase, CareerDispatchEffect)

    def test_subclass_with_literal_type_auto_registers(self):
        class _TestXyzHandler(CareerHandlerBase):
            type: Literal['_test_xyz'] = '_test_xyz'

        assert get_career_handler('_test_xyz') is _TestXyzHandler

    def test_intermediate_base_without_literal_type_does_not_register(self):
        class _TestIntermediateBase(CareerHandlerBase):
            pass

        class _TestConcreteHandler(_TestIntermediateBase):
            type: Literal['_test_intermediate_concrete'] = '_test_intermediate_concrete'

        assert get_career_handler('_test_intermediate_concrete') is _TestConcreteHandler
        # The intermediate base itself is not registered under any key
        assert get_career_handler('_TestIntermediateBase') is None

    def test_get_career_handler_returns_none_for_unknown_key(self):
        assert get_career_handler('no_such_handler_key') is None

    def test_handler_class_has_static_handle_method(self):
        class _TestHandleH(CareerHandlerBase):
            type: Literal['_test_handle_h'] = '_test_handle_h'

        assert callable(_TestHandleH.handle)

    def test_handler_class_has_static_resolve_method(self):
        class _TestResolveH(CareerHandlerBase):
            type: Literal['_test_resolve_h'] = '_test_resolve_h'

        assert callable(_TestResolveH.resolve)

    def test_handler_class_has_static_on_choice_method(self):
        class _TestChoiceH(CareerHandlerBase):
            type: Literal['_test_choice_h'] = '_test_choice_h'

        assert callable(_TestChoiceH.on_choice)

    def test_handler_base_handle_returns_pending_idx_unchanged(self):
        """Base handle() is a no-op returning pending_idx unchanged."""

        class _TestNoop(CareerHandlerBase):
            type: Literal['_test_noop'] = '_test_noop'

        from ceres.character.state import CharacterProjection

        assert _TestNoop.handle(cast(CharacterProjection, None), 0, 5) == 5

    def test_handler_instance_is_career_dispatch_effect(self):
        class _TestInstH(CareerHandlerBase):
            type: Literal['_test_inst_h'] = '_test_inst_h'

        assert isinstance(_TestInstH(), CareerDispatchEffect)

    def test_handler_instance_type_attribute_matches_literal(self):
        class _TestTypeAttr(CareerHandlerBase):
            type: Literal['_test_type_attr'] = '_test_type_attr'

        assert _TestTypeAttr().type == '_test_type_attr'


_ALL_EXPECTED_HANDLER_KEYS: list[str] = [
    # agent
    'agent_mishap_2',
    'agent_mishap_3',
    'agent_mishap_5',
    'agent_event_3',
    'agent_event_6',
    'agent_event_8',
    'agent_event_11',
    # army
    'army_mishap_4',
    'army_event_6',
    'army_event_8',
    # citizen
    'citizen_mishap_4',
    'citizen_mishap_5',
    'citizen_event_6',
    'citizen_event_8',
    'citizen_event_8_skill',
    # drifter
    'drifter_mishap_5',
    'drifter_event_3',
    'drifter_event_8',
    'drifter_event_9',
    'drifter_event_9_roll',
    'drifter_event_11',
    # entertainer
    'entertainer_event_3',
    'entertainer_event_8',
    'entertainer_event_8_skill',
    # marines
    'marines_mishap_4',
    'marines_mishap_4_skill',
    'marines_event_5',
    'marines_event_6',
    'marines_event_9',
    # merchant
    'merchant_event_3',
    'merchant_event_3_skill',
    'merchant_event_5',
    'merchant_event_8',
    'merchant_event_8_roll',
    'merchant_event_9',
    # navy
    'navy_mishap_3',
    'navy_mishap_4',
    'navy_event_5',
    'navy_event_10',
    # noble
    'noble_mishap_3',
    'noble_mishap_5',
    'noble_event_8',
    'noble_event_8_skill',
    # prisoner
    'prisoner_mishap_3',
    'prisoner_mishap_3_fight',
    'prisoner_event_3',
    'prisoner_event_3_escape',
    'prisoner_event_4',
    'prisoner_event_5',
    'prisoner_event_6',
    'prisoner_event_7',
    'prisoner_event_7_riot',
    'prisoner_event_9',
    'prisoner_event_9_level_1',
    'prisoner_event_9_level_2',
    'prisoner_event_9_level_3',
    'prisoner_event_12',
    'prisoner_event_12_heroism',
    # rogue
    'rogue_mishap_2',
    'rogue_mishap_3',
    'rogue_mishap_3_prisoner_check',
    'rogue_event_3',
    'rogue_event_3_skill',
    'rogue_event_6',
    'rogue_event_9',
    # scholar
    'scholar_event_3',
    'scholar_event_6',
    'scholar_event_8',
    'scholar_event_8_roll',
    'scholar_event_11',
    'scholar_mishap_3',
    'scholar_mishap_5',
    # scout
    'scout_event_3',
    'scout_event_8',
    'scout_event_9',
    'scout_event_10',
    'scout_event_11',
]


class TestCareerHandlerRegistrationCompleteness:
    @pytest.fixture(autouse=True)
    def _load_careers(self):
        from ceres.character.careers.loader import load_careers

        load_careers()

    @pytest.mark.parametrize('key', _ALL_EXPECTED_HANDLER_KEYS)
    def test_expected_handler_key_is_registered(self, key: str):
        handler_cls = get_career_handler(key)
        assert handler_cls is not None, f'No handler registered for {key!r}'
        assert issubclass(handler_cls, CareerHandlerBase)

    def test_no_raw_career_dispatch_effect_remains_in_any_career_effects(self):
        """After converting all career modules, effects should only use CareerHandlerBase subclasses."""
        from ceres.character.careers.loader import load_careers

        careers = load_careers()
        for career_name, career in careers.items():
            for roll, entry in career.events.items():
                for effect in entry.effects:
                    if isinstance(effect, CareerDispatchEffect):
                        assert isinstance(effect, CareerHandlerBase), (
                            f'{career_name} event {roll}: '
                            f'raw CareerDispatchEffect(type={effect.type!r}) found; '
                            f'replace with a CareerHandlerBase subclass'
                        )
            for roll, mishap in career.mishaps.items():
                for effect in mishap.effects:
                    if isinstance(effect, CareerDispatchEffect):
                        assert isinstance(effect, CareerHandlerBase), (
                            f'{career_name} mishap {roll}: '
                            f'raw CareerDispatchEffect(type={effect.type!r}) found; '
                            f'replace with a CareerHandlerBase subclass'
                        )

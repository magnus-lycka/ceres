"""Unit tests for character_start.py — creation handlers, UcpHandler, etc."""

import pytest

from ceres.character.domain.character_start import (
    BackgroundSkillsHandler,
    CharacterCreatedHandler,
    FinishCreationHandler,
    HomeworldSelectedHandler,
    PendingBackgroundSkills,
    PendingHomeworldSelection,
    PendingSophontSelection,
    PendingUcp,
    SophontSelectedHandler,
    UcpHandler,
    _background_skill_count,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Animals, Carouse, Drive
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


def _any_event() -> Event:
    from ceres.character.domain.career.career_events import SurviveHandler

    return Event(handler=SurviveHandler(roll=5))


class TestBackgroundSkillCount:
    def test_edu_7_returns_3(self):
        assert _background_skill_count(7) == 3

    def test_edu_4_returns_2(self):
        assert _background_skill_count(4) == 2

    def test_edu_2_returns_1(self):
        assert _background_skill_count(2) == 1

    def test_edu_0_returns_0(self):
        assert _background_skill_count(0) == 0

    def test_negative_edu_clamped_to_0(self):
        assert _background_skill_count(-5) == 0


class TestUcpHandler:
    def _proj_with_ucp(self, ucp: str) -> CharacterProjection:
        proj = _projection()
        handler = UcpHandler(ucp=ucp)
        proj.pending_inputs = []
        handler.apply(proj, _any_event())
        return proj

    def test_parses_six_hex_digits(self):
        proj = self._proj_with_ucp('777777')
        assert proj.summary.characteristics[Chars.STR] == 7
        assert proj.summary.characteristics[Chars.EDU] == 7

    def test_high_edu_queues_background_skills(self):
        proj = self._proj_with_ucp('7777A7')  # EDU=10, dm=1, count=4
        assert any(isinstance(p, PendingBackgroundSkills) for p in proj.pending_inputs)

    def test_wrong_length_raises(self):
        proj = _projection()
        with pytest.raises(ReplayError, match='Invalid UCP'):
            UcpHandler(ucp='777').apply(proj, _any_event())


class TestBackgroundSkillsHandler:
    def _proj_with_edu(self, edu: int) -> CharacterProjection:
        proj = _projection()
        proj.summary.characteristics = {
            Chars.STR: 7,
            Chars.DEX: 7,
            Chars.END: 7,
            Chars.INT: 7,
            Chars.EDU: edu,
            Chars.SOC: 7,
        }
        return proj

    def test_grants_all_background_skills(self):
        proj = self._proj_with_edu(7)  # count=3
        handler = BackgroundSkillsHandler(skills=[Animals(), Carouse(), Drive()])
        proj.pending_inputs = []
        handler.apply(proj, _any_event())
        assert proj.summary.skill_level(Animals, 0) == 0
        assert proj.summary.skill_level(Carouse, 0) == 0

    def test_wrong_count_raises(self):
        proj = self._proj_with_edu(7)
        handler = BackgroundSkillsHandler(skills=[Admin()])
        with pytest.raises(ReplayError, match='Expected 3 background skill'):
            handler.apply(proj, _any_event())

    def test_non_background_skill_raises(self):
        from ceres.character.domain.skills import JackOfAllTrades

        proj = self._proj_with_edu(4)  # count=2
        handler = BackgroundSkillsHandler(skills=[Admin(), JackOfAllTrades()])
        with pytest.raises(ReplayError, match='Invalid background skill'):
            handler.apply(proj, _any_event())


class TestPendingUcp:
    def test_event_from_form_builds_ucp_string(self):
        pending = PendingUcp(pending_id=(1, 0), instruction='UCP')
        event = pending.event_from_form({'STR': '7', 'DEX': '7', 'END': '7', 'INT': '7', 'EDU': '7', 'SOC': '7'})
        assert isinstance(event.handler, UcpHandler)
        assert event.handler.ucp == '777777'

    def test_input_specs_returns_number_entries(self):
        pending = PendingUcp(pending_id=(1, 0), instruction='UCP')
        specs = pending.input_specs(_projection())
        assert all(isinstance(s, NumberEntry) for s in specs)
        assert len(specs) == 6


class TestPendingBackgroundSkills:
    def test_input_specs_returns_select_with_multiple(self):
        proj = _projection()
        proj.summary.characteristics = {
            Chars.STR: 7,
            Chars.DEX: 7,
            Chars.END: 7,
            Chars.INT: 7,
            Chars.EDU: 7,
            Chars.SOC: 7,
        }
        from ceres.character.domain.skills import AnySkill as _AnySkill

        options: list[_AnySkill] = [Animals(), Carouse()]
        pending = PendingBackgroundSkills(
            pending_id=(1, 0), instruction='Choose 2 background skill(s)', options=options
        )
        specs = pending.input_specs(proj)
        assert len(specs) == 1
        assert isinstance(specs[0], Select)
        assert specs[0].min_select == 2


class TestCharacterCreatedHandler:
    def test_creates_projection_with_correct_name(self):
        proj = CharacterCreatedHandler(name='Ada', player='NPC').init_replay(1, 1)
        assert proj.summary.name == 'Ada'

    def test_has_no_sophont_yet(self):
        proj = CharacterCreatedHandler(name='Ada', player='NPC').init_replay(1, 1)
        assert proj.summary.sophont is None

    def test_has_no_homeworld_yet(self):
        proj = CharacterCreatedHandler(name='Ada', player='NPC').init_replay(1, 1)
        assert proj.summary.homeworld is None

    def test_adds_blocking_pending_homeworld_selection(self):
        proj = CharacterCreatedHandler(name='Ada', player='NPC').init_replay(1, 1)
        assert len(proj.pending_inputs) == 1
        pending = proj.pending_inputs[0]
        assert isinstance(pending, PendingHomeworldSelection)
        assert pending.blocking


class TestHomeworldSelectedHandler:
    def _proj_after_homeworld(self):
        from ceres.character.mechanism.replay import replay

        ev1 = Event(handler=CharacterCreatedHandler(name='Ada', player='NPC'))
        ev2 = Event(fulfills=(ev1.id, 0), handler=HomeworldSelectedHandler(homeworld=MOCK_WORLD))
        return replay(1, [ev1, ev2])

    def test_sets_homeworld(self):
        assert self._proj_after_homeworld().summary.homeworld == MOCK_WORLD

    def test_sets_birthworld(self):
        assert self._proj_after_homeworld().summary.birthworld == MOCK_WORLD

    def test_adds_blocking_pending_sophont_selection(self):
        proj = self._proj_after_homeworld()
        sophont_pending = next((p for p in proj.pending_inputs if isinstance(p, PendingSophontSelection)), None)
        assert sophont_pending is not None
        assert sophont_pending.blocking


class TestSophontSelectedHandler:
    def _proj_after_sophont(self):
        from ceres.character.mechanism.replay import replay

        ev1 = Event(handler=CharacterCreatedHandler(name='Ada', player='NPC'))
        ev2 = Event(fulfills=(ev1.id, 0), handler=HomeworldSelectedHandler(homeworld=MOCK_WORLD))
        ev3 = Event(fulfills=(ev2.id, 0), handler=SophontSelectedHandler(sophont=VILANI))
        return replay(1, [ev1, ev2, ev3])

    def test_sets_sophont(self):
        assert self._proj_after_sophont().summary.sophont is VILANI

    def test_adds_pending_ucp(self):
        proj = self._proj_after_sophont()
        assert any(isinstance(p, PendingUcp) for p in proj.pending_inputs)

    def test_sophont_coerced_from_string(self):
        handler = SophontSelectedHandler.model_validate({'sophont': 'Vilani'})
        assert handler.sophont is VILANI

    def test_unknown_sophont_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SophontSelectedHandler.model_validate({'sophont': 'NotARealSophont'})


class TestFinishCreationHandler:
    def test_removes_homeworld_change_pending(self):
        from ceres.character.domain.career.career_events import PendingSurvive
        from ceres.character.domain.homeworld.homeworld_events import PendingHomeworldChangeOffered

        proj = _projection()
        proj.pending_inputs = [
            PendingHomeworldChangeOffered(pending_id=(2, 0), instruction='Change homeworld?', reason='Test'),
            PendingSurvive(pending_id=(3, 0), instruction='Survive'),
        ]
        FinishCreationHandler().apply(proj, _any_event())
        assert not any(isinstance(p, PendingHomeworldChangeOffered) for p in proj.pending_inputs)
        assert any(isinstance(p, PendingSurvive) for p in proj.pending_inputs)

"""Unit tests for skill_events.py — SkillChoiceHandler, PendingSkillChoice, helpers."""

from ceres.character.domain.career.career_data import AdvancementDmOption
from ceres.character.domain.career.career_events import SurviveHandler
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.skill_events import (
    PendingSkillChoice,
    SkillChoiceHandler,
    build_skill_select_options,
)
from ceres.character.domain.skills import Admin, Level
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import Select
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


def _any_event() -> Event:
    return Event(handler=SurviveHandler(roll=5))


class TestOptionSelectOptions:
    """Each option type builds its own (label, form_value) pairs; the builder just flattens."""

    def test_skill_expands_via_projection(self):
        proj = _projection()
        options = Admin().select_options(proj, None)
        assert len(options) == 1
        label, json_val = options[0]
        assert label == 'Admin'
        assert Admin.model_validate_json(json_val).level.value == 1

    def test_advancement_dm_offers_itself(self):
        opt = AdvancementDmOption()
        assert opt.select_options(_projection(), None) == [(opt.label(), opt.model_dump_json())]

    def test_entry_offers_itself(self):
        from ceres.character.domain.career.skill_table_entries import Skill as SkillEntry

        entry = SkillEntry(Admin)
        assert entry.select_options(_projection(), None) == [(entry.label(), entry.model_dump_json())]

    def test_entry_chosen_handler_wraps_itself(self):
        from ceres.character.domain.career.career_events import SkillTableEntryChosenHandler
        from ceres.character.domain.career.skill_table_entries import Skill as SkillEntry

        entry = SkillEntry(Admin)
        handler = entry.chosen_handler()
        assert isinstance(handler, SkillTableEntryChosenHandler)
        assert handler.entry is entry

    def test_advancement_dm_chosen_handler(self):
        from ceres.character.domain.career.advancement import AdvancementDmChoiceHandler

        assert isinstance(AdvancementDmOption().chosen_handler(), AdvancementDmChoiceHandler)


class TestOptionIsAvailable:
    """A rank-bonus choice knows whether it can still benefit this character."""

    def test_unknown_skill_is_available_at_level_one(self):
        assert Admin().is_available(_projection(), 1) is True

    def test_skill_already_at_level_is_not_available(self):
        proj = _projection()
        proj.summary.skills.append(Admin(level=Level(value=1)))
        assert Admin().is_available(proj, 1) is False

    def test_psi_entry_is_always_available(self):
        from ceres.character.domain.career.skill_table_entries import Psi as PsiEntry
        from ceres.character.domain.psionics_data import Telepathy

        assert PsiEntry(Telepathy, allow_acquisition=True).is_available(_projection(), 1) is True


class TestBuildSkillSelectOptions:
    def test_non_specialised_level_zero(self):
        proj = _projection()
        options = build_skill_select_options(proj, [Admin()], 0)
        assert len(options) == 1
        label, json_val = options[0]
        assert label == 'Admin'
        assert Admin.model_validate_json(json_val) is not None

    def test_advancement_dm_option(self):
        proj = _projection()
        opt = AdvancementDmOption()
        options = build_skill_select_options(proj, [opt], None)
        assert any(opt.label() in label for label, _ in options)

    def test_level_none_non_specialised_at_0_offers_level_1(self):
        proj = _projection()
        options = build_skill_select_options(proj, [Admin()], None)
        assert len(options) == 1


class TestSkillChoiceHandler:
    def test_grants_skill_when_no_on_skill_chosen(self):
        proj = _projection()
        handler = SkillChoiceHandler(skill=Admin(level=Level(value=1)))
        handler.apply(proj, _any_event())
        assert proj.summary.skill_level(Admin, 0) == 1

    def test_delegates_to_on_skill_chosen_when_present(self):
        from ceres.character.domain.life_events import PendingLifeEventAlienScience

        proj = _projection()
        pending = PendingLifeEventAlienScience(pending_id=(1, 0), instruction='Choose')
        admin = Admin(level=Level(value=1))
        event = Event(handler=SkillChoiceHandler(skill=admin))
        SkillChoiceHandler(skill=admin).apply(proj, event, fulfilled_pending=pending)
        assert proj.summary.skill_level(Admin, 0) == 1


class TestPendingSkillChoice:
    def test_event_from_form_parses_skill(self):
        pending = PendingSkillChoice(pending_id=(1, 0), instruction='Choose', options=[Admin()])
        event = pending.event_from_form({'skill': Admin().model_dump_json()})
        assert isinstance(event.handler, SkillChoiceHandler)
        assert isinstance(event.handler.skill, Admin)

    def test_event_from_form_advancement_dm(self):
        from ceres.character.domain.career.advancement import AdvancementDmChoiceHandler

        opt = AdvancementDmOption()
        pending = PendingSkillChoice(pending_id=(1, 0), instruction='Choose', options=[Admin()])
        event = pending.event_from_form({'skill': opt.model_dump_json()})
        assert isinstance(event.handler, AdvancementDmChoiceHandler)

    def test_input_specs_returns_select(self):
        pending = PendingSkillChoice(pending_id=(1, 0), instruction='Choose', options=[Admin()])
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], Select) and specs[0].name == 'skill'

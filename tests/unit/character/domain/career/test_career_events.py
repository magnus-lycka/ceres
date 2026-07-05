"""Unit tests for career_events pending input mechanics."""

from typing import Literal

import pytest

from ceres.character.domain.career import ARMY
from ceres.character.domain.career.career_data import SkillTableOption
from ceres.character.domain.career.career_events import (
    AssignmentChangeChoiceHandler,
    MishapHandler,
    PendingAssignmentChangeChoice,
    PendingInitialTrainingChoice,
    PendingMishap,
    PendingRankBonusChoice,
    PendingReenlist,
    PendingSkillTable,
    PendingSkillTableChoice,
    PendingSurvive,
    PendingSwitchAssignment,
    PendingTermEvent,
    ReenlistHandler,
    SkillChoiceHandler,
    SkillRollHandler,
    SkillTableEntryChosenHandler,
    SkillTableHandler,
    SurviveHandler,
    SwitchAssignmentHandler,
    TermEventHandler,
    purge_career_pendings,
    queue_reenlist_or_aging,
)
from ceres.character.domain.career.entry import PendingCareerChoice
from ceres.character.domain.career.skill_table_entries import Char
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin, Level
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.errors import ReplayError
from ceres.character.mechanism.event_base import Event, PendingInputBase
from tests.unit.character.helpers import MOCK_WORLD


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


def _event(roll: int = 5) -> Event:
    return Event(handler=SurviveHandler(roll=roll))


def _projection_with_army(
    assignment_name: str = 'Infantry',
    **kwargs,
) -> CharacterProjection:
    from ceres.character.domain.career.career_data import CareerTerm

    proj = _projection(**kwargs)
    proj.summary.terms.append(CareerTerm(career=ARMY, assignment=ARMY.assignment(assignment_name)))
    return proj


class _NoopPending(PendingInputBase):
    kind: Literal['noop_pending'] = 'noop_pending'

    def event_from_form(self, form):
        raise NotImplementedError

    def input_specs(self, projection):
        return []


class TestPendingSurvive:
    def test_event_from_form_parses_roll(self):
        pending = PendingSurvive(pending_id=(1, 0), instruction='Roll 2D')
        event = pending.event_from_form({'roll': '8'})
        assert isinstance(event.handler, SurviveHandler)
        assert event.handler.roll == 8

    def test_event_from_form_defaults_roll(self):
        pending = PendingSurvive(pending_id=(1, 0), instruction='Roll 2D')
        event = pending.event_from_form({})
        assert isinstance(event.handler, SurviveHandler)
        assert event.handler.roll == 2

    def test_input_specs_returns_roll_entry(self):
        pending = PendingSurvive(pending_id=(1, 0), instruction='Roll 2D')
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], NumberEntry)
        assert specs[0].min == 2 and specs[0].max == 12

    def test_resolve_natural_2_queues_mishap_with_narrative(self):
        from ceres.character.domain.career.career_data import CareerTerm

        proj = _projection()
        proj.summary.terms.append(CareerTerm(career=ARMY, assignment=ARMY.assignment('Infantry')))
        pending = PendingSurvive(pending_id=(1, 0), instruction='Roll 2D')
        event = pending.event_from_form({'roll': '2'})
        pending.resolve(proj, event)
        assert any(isinstance(p, PendingMishap) for p in proj.pending_inputs)
        assert any('natural 2' in n for n in proj.summary.narrative)

    def test_resolve_raises_when_no_current_assignment(self):
        import pytest

        from ceres.character.mechanism.errors import ReplayError

        proj = _projection()
        pending = PendingSurvive(pending_id=(1, 0), instruction='Roll 2D')
        event = pending.event_from_form({'roll': '8'})
        with pytest.raises(ReplayError, match='No current assignment'):
            pending.resolve(proj, event)


class TestPendingTermEvent:
    def test_event_from_form_parses_roll(self):
        pending = PendingTermEvent(pending_id=(1, 0), instruction='Roll 2D on Events table')
        event = pending.event_from_form({'roll': '7'})
        assert isinstance(event.handler, TermEventHandler)
        assert event.handler.roll == 7

    def test_event_from_form_defaults_roll(self):
        pending = PendingTermEvent(pending_id=(1, 0), instruction='Roll 2D on Events table')
        event = pending.event_from_form({})
        assert isinstance(event.handler, TermEventHandler)
        assert event.handler.roll == 2

    def test_input_specs_returns_roll_entry(self):
        pending = PendingTermEvent(pending_id=(1, 0), instruction='Roll 2D on Events table')
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], NumberEntry)


class TestSurviveHandler:
    def test_apply_delegates_to_fulfilled_pending(self):
        proj = _projection_with_army(characteristics={Chars.STR: 12})
        pending = PendingSurvive(pending_id=(1, 0), instruction='Roll 2D')
        event = Event(id=7, handler=SurviveHandler(roll=8))

        event.apply(proj, fulfilled_pending=pending)

        assert any(isinstance(p, PendingTermEvent) for p in proj.pending_inputs)


class TestPendingMishap:
    def test_event_from_form_parses_roll(self):
        pending = PendingMishap(pending_id=(1, 0), instruction='Roll 1D on Mishap table')
        event = pending.event_from_form({'roll': '3'})
        assert isinstance(event.handler, MishapHandler)
        assert event.handler.roll == 3

    def test_event_from_form_propagates_stay_in_career(self):
        pending = PendingMishap(pending_id=(1, 0), instruction='Roll 1D', stay_in_career=True)
        event = pending.event_from_form({'roll': '1'})
        assert isinstance(event.handler, MishapHandler)
        assert event.handler.stay_in_career is True

    def test_input_specs_returns_1d_roll(self):
        pending = PendingMishap(pending_id=(1, 0), instruction='Roll 1D')
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], NumberEntry)
        assert specs[0].min == 1 and specs[0].max == 6


class TestMishapHandler:
    def test_mishap_text_is_recorded_and_deferred_mishap_does_not_eject(self):
        proj = _projection_with_army()
        event = Event(id=11, handler=MishapHandler(roll=1))

        event.apply(proj)

        assert any('Severely injured' in problem for problem in proj.summary.problems)
        assert any('Mishap (Army)' in note for note in proj.summary.narrative)
        assert proj.summary.current_career is ARMY

    def test_stay_in_career_queues_advancement_after_mishap(self):
        from ceres.character.domain.career.advancement import PendingAdvancement

        proj = _projection_with_army()
        event = Event(id=11, handler=MishapHandler(roll=2, stay_in_career=True))

        event.apply(proj)

        assert any(isinstance(p, PendingAdvancement) for p in proj.pending_inputs)

    def test_ejecting_mishap_records_mishap_and_sets_up_muster_out(self):
        proj = _projection_with_army()
        event = Event(id=11, handler=MishapHandler(roll=2))

        event.apply(proj)

        term = proj.summary.career_terms[-1]
        assert term.mishap is not None
        assert term.require_muster_out().lost_rolls == 1
        assert proj.summary.last_career is ARMY
        assert proj.summary.last_career_ejected is True
        assert any(isinstance(p, PendingCareerChoice) for p in proj.pending_inputs)

    def test_unknown_mishap_roll_still_ejects_and_sets_up_muster_out(self):
        proj = _projection_with_army()
        event = Event(id=11, handler=MishapHandler(roll=99))

        event.apply(proj)

        assert proj.summary.last_career is ARMY
        assert proj.summary.last_career_ejected is True
        assert any(isinstance(p, PendingCareerChoice) for p in proj.pending_inputs)


class TestPendingSkillTable:
    def test_event_from_form_parses_table_and_roll(self):
        pending = PendingSkillTable(
            pending_id=(1, 0),
            instruction='Choose a table',
            options=[SkillTableOption(label='Service Skills', key='service_skills')],
        )
        event = pending.event_from_form({'table': 'service_skills', 'roll': '4'})
        assert isinstance(event.handler, SkillTableHandler)
        assert event.handler.table == 'service_skills'
        assert event.handler.roll == 4

    def test_input_specs_includes_table_select_and_roll(self):
        pending = PendingSkillTable(
            pending_id=(1, 0),
            instruction='Choose a table',
            options=[
                SkillTableOption(label='Service Skills', key='service_skills'),
                SkillTableOption(label='Personal Development', key='personal_development'),
            ],
        )
        specs = pending.input_specs(_projection())
        assert len(specs) == 2
        assert isinstance(specs[0], Select) and specs[0].name == 'table'
        assert isinstance(specs[1], NumberEntry) and specs[1].name == 'roll'


class TestSkillTableHandlerOrdering:
    def _proj_with_army_career(self) -> CharacterProjection:
        from ceres.character.domain.career.career_data import CareerTerm

        proj = _projection()
        proj.summary.terms.append(CareerTerm(career=ARMY, assignment=ARMY.assignment('Infantry')))
        return proj

    def test_skill_choice_inserted_before_survive_pending(self):
        """SkillTableHandler must insert PendingSkillTableChoice before any PendingSurvive in the queue."""
        from ceres.character.domain.career.career_events import PendingSkillTableChoice

        proj = self._proj_with_army_career()
        survive = PendingSurvive(pending_id=(99, 0), instruction='Survive!')
        proj.queue_deferred(survive)

        event = PendingSkillTable(
            pending_id=(1, 0),
            instruction='Choose a table',
            options=[SkillTableOption(label='Service Skills', key='service_skills')],
        ).event_from_form({'table': 'service_skills', 'roll': '1'})
        event.apply(proj)

        pending_types = [type(p) for p in proj.pending_inputs]
        choice_idx = pending_types.index(PendingSkillTableChoice)
        survive_idx = pending_types.index(PendingSurvive)
        assert choice_idx < survive_idx, 'Skill table choice must come before survive pending'

    def test_rank_bonus_skill_table_inserted_before_survive_pending(self):
        """Rank bonus skill table roll must come before PendingSurvive — rank is gained during the term."""
        from ceres.character.domain.career.career_events import PendingRankBonusChoice

        proj = self._proj_with_army_career()
        survive = PendingSurvive(pending_id=(99, 0), instruction='Survive!')
        proj.queue_deferred(survive)

        pending = PendingRankBonusChoice(
            pending_id=(1, 0),
            instruction='Choose rank bonus skill',
            options=[Admin()],
            level=1,
        )
        event = pending.event_from_form({'skill': '{"kind": "ADMIN"}'})
        event.apply(proj, fulfilled_pending=pending)

        pending_types = [type(p) for p in proj.pending_inputs]
        assert PendingSkillTable in pending_types, 'PendingSkillTable should be queued by _continue()'
        skill_table_idx = pending_types.index(PendingSkillTable)
        survive_idx = pending_types.index(PendingSurvive)
        assert skill_table_idx < survive_idx, 'Rank bonus skill table must come before survive pending'


class TestSkillTableHandlerGuardrails:
    def _proj_with_army_career(self, **kwargs) -> CharacterProjection:
        from ceres.character.domain.career.career_data import CareerTerm

        proj = _projection(**kwargs)
        proj.summary.terms.append(CareerTerm(career=ARMY, assignment=ARMY.assignment('Infantry')))
        return proj

    def test_unknown_table_raises(self):
        proj = self._proj_with_army_career()
        event = Event(id=10, handler=SkillTableHandler(table='missing_table', roll=1))

        with pytest.raises(ReplayError, match='Unknown skill table'):
            event.apply(proj)

    def test_advanced_education_requires_minimum_edu(self):
        proj = self._proj_with_army_career(characteristics={})
        event = Event(id=10, handler=SkillTableHandler(table='advanced_education', roll=1))

        with pytest.raises(ReplayError, match='requires EDU 8\\+'):
            event.apply(proj)

    def test_roll_outside_1_to_6_raises(self):
        proj = self._proj_with_army_career()
        event = Event(id=10, handler=SkillTableHandler(table='personal_development', roll=7))

        with pytest.raises(ReplayError, match='Skill table roll must be 1-6'):
            event.apply(proj)


class TestSkillTableEntryChosenHandler:
    def test_applies_chosen_skill_table_entry(self):
        proj = _projection(characteristics={Chars.STR: 7})
        event = Event(id=10, handler=SkillTableEntryChosenHandler(entry=Char(Chars.STR)))

        event.apply(proj)

        assert proj.summary.characteristics[Chars.STR] == 8


class TestTermEventHandler:
    def test_event_records_narrative_term_text_and_continues_career_progress(self):
        from ceres.character.domain.career.advancement import PendingCommissionChoice

        proj = _projection_with_army('Support')
        event = Event(id=12, handler=TermEventHandler(roll=5))

        event.apply(proj)

        assert any('Term 1 event (Army)' in note for note in proj.summary.narrative)
        assert 'special assignment' in (proj.summary.career_terms[-1].event or '')
        assert any(isinstance(p, PendingCommissionChoice) for p in proj.pending_inputs)

    def test_event_handler_that_queues_pending_does_not_also_queue_career_progress(self):
        proj = _projection_with_army()
        event = Event(id=12, handler=TermEventHandler(roll=6))

        event.apply(proj)

        assert any(p.pending_id == (12, 0) for p in proj.pending_inputs)
        assert len(proj.pending_inputs) == 1

    def test_unknown_event_roll_still_queues_career_progress(self):
        from ceres.character.domain.career.advancement import PendingCommissionChoice

        proj = _projection_with_army('Support')
        event = Event(id=12, handler=TermEventHandler(roll=99))

        event.apply(proj)

        assert any(isinstance(p, PendingCommissionChoice) for p in proj.pending_inputs)


class TestPendingReenlist:
    def test_event_from_form_reenlist_true(self):
        pending = PendingReenlist(pending_id=(1, 0))
        event = pending.event_from_form({'reenlist': 'true'})
        assert isinstance(event.handler, ReenlistHandler)
        assert event.handler.reenlist is True

    def test_event_from_form_reenlist_false(self):
        pending = PendingReenlist(pending_id=(1, 0))
        event = pending.event_from_form({'reenlist': 'false'})
        assert isinstance(event.handler, ReenlistHandler)
        assert event.handler.reenlist is False

    def test_event_from_form_defaults_to_false(self):
        pending = PendingReenlist(pending_id=(1, 0))
        event = pending.event_from_form({})
        assert isinstance(event.handler, ReenlistHandler)
        assert event.handler.reenlist is False

    def test_template_fragment_is_reenlist(self):
        assert PendingReenlist(pending_id=(1, 0)).template_fragment == 'reenlist'

    def test_input_specs_returns_empty(self):
        assert PendingReenlist(pending_id=(1, 0)).input_specs(_projection()) == []


class TestReenlistHandler:
    def test_reenlist_starts_new_term(self):
        proj = _projection_with_army()
        event = Event(id=13, handler=ReenlistHandler(reenlist=True))

        event.apply(proj)

        assert len(proj.summary.career_terms) == 2
        assert any(isinstance(p, PendingSurvive) for p in proj.pending_inputs)

    def test_muster_out_choice_sets_up_muster_out(self):
        from ceres.character.domain.career.muster_out import PendingMusterOut

        proj = _projection_with_army()
        event = Event(id=13, handler=ReenlistHandler(reenlist=False))

        event.apply(proj)

        assert any(isinstance(p, PendingMusterOut) for p in proj.pending_inputs)


class TestSkillRollHandler:
    def test_resolving_without_new_blocking_pending_queues_advancement(self):
        from ceres.character.domain.career.advancement import PendingAdvancement

        proj = _projection_with_army()
        pending = _NoopPending(pending_id=(1, 0), instruction='No-op')
        event = Event(id=14, handler=SkillRollHandler(skill=Admin(), modified_roll=8))

        event.apply(proj, fulfilled_pending=pending)

        assert any(isinstance(p, PendingAdvancement) for p in proj.pending_inputs)

    def test_existing_advancement_pending_prevents_duplicate_advancement(self):
        from ceres.character.domain.career.advancement import PendingAdvancement

        proj = _projection_with_army()
        existing = PendingAdvancement(pending_id=(99, 0), instruction='Already queued')
        proj.queue_deferred(existing)
        event = Event(id=14, handler=SkillRollHandler(skill=Admin(), modified_roll=8))

        event.apply(proj, fulfilled_pending=None)

        assert [p for p in proj.pending_inputs if isinstance(p, PendingAdvancement)] == [existing]


class TestAssignmentChangeChoiceHandler:
    def _proj_with_army(self) -> CharacterProjection:
        from ceres.character.domain.career.career_data import CareerTerm

        proj = _projection()
        proj.summary.terms.append(CareerTerm(career=ARMY, assignment=ARMY.assignment('Infantry')))
        return proj

    def test_switch_choice_queues_pending_switch_assignment(self):
        proj = self._proj_with_army()
        event = Event(handler=SurviveHandler(roll=5))
        AssignmentChangeChoiceHandler(choice='switch').apply(proj, event)
        assert any(isinstance(p, PendingSwitchAssignment) for p in proj.pending_inputs)

    def test_switch_excludes_current_assignment_from_options(self):
        proj = self._proj_with_army()
        event = Event(handler=SurviveHandler(roll=5))
        AssignmentChangeChoiceHandler(choice='switch').apply(proj, event)
        switch = next(p for p in proj.pending_inputs if isinstance(p, PendingSwitchAssignment))
        names = [a.name for a in switch.options]
        assert 'Infantry' not in names

    def test_same_choice_starts_new_term(self):
        proj = self._proj_with_army()
        event = Event(id=15, handler=AssignmentChangeChoiceHandler(choice='same'))

        event.apply(proj)

        assert len(proj.summary.career_terms) == 2

    def test_muster_out_choice_sets_up_muster_out(self):
        from ceres.character.domain.career.muster_out import PendingMusterOut

        proj = self._proj_with_army()
        event = Event(id=15, handler=AssignmentChangeChoiceHandler(choice='muster_out'))

        event.apply(proj)

        assert any(isinstance(p, PendingMusterOut) for p in proj.pending_inputs)


class TestSwitchAssignmentHandler:
    def _proj_with_army(self) -> CharacterProjection:
        from ceres.character.domain.career.career_data import CareerTerm

        proj = _projection()
        proj.summary.terms.append(CareerTerm(career=ARMY, assignment=ARMY.assignment('Infantry')))
        return proj

    def test_failed_qualification_queues_reenlist(self):
        proj = self._proj_with_army()
        event = Event(handler=SurviveHandler(roll=5))
        handler = SwitchAssignmentHandler(assignment=ARMY.assignment('Support'), qualification_roll=2)
        handler.apply(proj, event)
        assert any(isinstance(p, PendingReenlist) for p in proj.pending_inputs)

    def test_successful_qualification_starts_new_term(self):
        proj = self._proj_with_army()
        event = Event(handler=SurviveHandler(roll=5))
        handler = SwitchAssignmentHandler(assignment=ARMY.assignment('Support'), qualification_roll=12)
        before_len = len(proj.summary.terms)
        handler.apply(proj, event)
        assert len(proj.summary.terms) > before_len

    def test_failed_qualification_without_current_assignment_raises(self):
        proj = _projection()
        event = Event(handler=SurviveHandler(roll=5))
        handler = SwitchAssignmentHandler(assignment=ARMY.assignment('Support'), qualification_roll=2)

        with pytest.raises(ReplayError, match='No active career'):
            handler.apply(proj, event)


class TestPendingAssignmentChangeChoice:
    def test_event_from_form_same(self):
        pending = PendingAssignmentChangeChoice(pending_id=(1, 0), instruction='Stay or switch?', muster_out=True)
        event = pending.event_from_form({'choice': 'same'})
        assert isinstance(event.handler, AssignmentChangeChoiceHandler)
        assert event.handler.choice == 'same'

    def test_event_from_form_muster_out(self):
        pending = PendingAssignmentChangeChoice(pending_id=(1, 0), instruction='Stay or switch?', muster_out=True)
        event = pending.event_from_form({'choice': 'muster_out'})
        assert isinstance(event.handler, AssignmentChangeChoiceHandler)
        assert event.handler.choice == 'muster_out'

    def test_input_specs_without_muster_out_excludes_muster_option(self):
        pending = PendingAssignmentChangeChoice(pending_id=(1, 0), instruction='Stay or switch?', muster_out=False)
        specs = pending.input_specs(_projection())
        assert len(specs) == 1
        assert isinstance(specs[0], Select)
        values = [v for _, v in specs[0].options]
        assert 'muster_out' not in values

    def test_input_specs_with_muster_out_includes_all_three_options(self):
        pending = PendingAssignmentChangeChoice(pending_id=(1, 0), instruction='Stay or switch?', muster_out=True)
        specs = pending.input_specs(_projection())
        assert isinstance(specs[0], Select)
        values = [v for _, v in specs[0].options]
        assert 'same' in values and 'switch' in values and 'muster_out' in values


class TestPendingSwitchAssignment:
    def test_event_from_form_selects_assignment(self):
        assignment = ARMY.assignment('Support')
        pending = PendingSwitchAssignment(pending_id=(1, 0), instruction='Switch?', options=[assignment])
        event = pending.event_from_form({'assignment': 'Support', 'roll': '6'})
        assert isinstance(event.handler, SwitchAssignmentHandler)
        assert event.handler.assignment == assignment
        assert event.handler.qualification_roll == 6

    def test_input_specs_returns_select_and_roll(self):
        pending = PendingSwitchAssignment(
            pending_id=(1, 0),
            instruction='Switch?',
            options=[ARMY.assignment('Support'), ARMY.assignment('Infantry')],
        )
        specs = pending.input_specs(_projection())
        assert len(specs) == 2
        assert isinstance(specs[0], Select) and specs[0].name == 'assignment'
        assert isinstance(specs[1], NumberEntry) and specs[1].name == 'roll'

    def test_event_from_form_unknown_assignment_raises(self):
        import pytest

        from ceres.character.mechanism.errors import ReplayError

        pending = PendingSwitchAssignment(
            pending_id=(1, 0), instruction='Switch?', options=[ARMY.assignment('Support')]
        )
        with pytest.raises(ReplayError, match='Unknown assignment'):
            pending.event_from_form({'assignment': 'Nonexistent', 'roll': '6'})


class TestPendingSkillOrPsiChoices:
    def test_initial_training_choice_input_specs_offer_select(self):
        pending = PendingInitialTrainingChoice(
            pending_id=(1, 0),
            instruction='Choose',
            options=[Admin()],
        )

        specs = pending.input_specs(_projection())

        assert len(specs) == 1
        assert isinstance(specs[0], Select)
        assert specs[0].name == 'skill'

    def test_initial_training_choice_event_from_form_returns_skill_choice(self):
        pending = PendingInitialTrainingChoice(
            pending_id=(1, 0),
            instruction='Choose',
            options=[Admin()],
        )

        event = pending.event_from_form({'skill': Admin().model_dump_json()})

        assert event.fulfills == (1, 0)
        assert isinstance(event.handler, SkillChoiceHandler)
        assert isinstance(event.handler.skill, Admin)

    def test_initial_training_choice_event_from_form_returns_entry_choice(self):
        pending = PendingInitialTrainingChoice(
            pending_id=(1, 0),
            instruction='Choose',
            options=[Char(Chars.STR)],
        )

        event = pending.event_from_form({'skill': Char(Chars.STR).model_dump_json()})

        assert event.fulfills == (1, 0)
        assert isinstance(event.handler, SkillTableEntryChosenHandler)
        assert isinstance(event.handler.entry, Char)

    def test_initial_training_choice_grants_skill(self):
        proj = _projection()
        pending = PendingInitialTrainingChoice(pending_id=(1, 0), instruction='Choose', options=[Admin()])
        event = pending.event_from_form({'skill': Admin(level=Level(value=1)).model_dump_json()})

        pending.on_skill_chosen(proj, event)

        assert proj.summary.skill_level(Admin, 0) == 1

    def test_initial_training_psi_choice_is_noop(self):
        proj = _projection()
        pending = PendingInitialTrainingChoice(pending_id=(1, 0), instruction='Choose', options=[Admin()])
        event = Event(id=17, handler=SurviveHandler(roll=8))

        pending.on_psi_chosen(proj, event)

        assert proj.pending_inputs == ()

    def test_skill_table_choice_grants_skill(self):
        proj = _projection()
        pending = PendingSkillTableChoice(
            pending_id=(1, 0),
            instruction='Choose',
            options=[Admin()],
            level=1,
        )
        event = pending.event_from_form({'skill': Admin(level=Level(value=1)).model_dump_json()})

        pending.on_skill_chosen(proj, event)

        assert proj.summary.skill_level(Admin, 0) == 1

    def test_skill_table_psi_choice_is_noop(self):
        proj = _projection()
        pending = PendingSkillTableChoice(
            pending_id=(1, 0),
            instruction='Choose',
            options=[Admin()],
            level=1,
        )
        event = Event(id=17, handler=SurviveHandler(roll=8))

        pending.on_psi_chosen(proj, event)

        assert proj.pending_inputs == ()

    def test_rank_bonus_input_specs_offer_select_without_psi_roll_for_skills(self):
        pending = PendingRankBonusChoice(
            pending_id=(1, 0),
            instruction='Choose',
            options=[Admin()],
            level=1,
        )

        specs = pending.input_specs(_projection())

        assert len(specs) == 1
        assert isinstance(specs[0], Select)

    def test_rank_bonus_choice_can_stop_career_progress(self):
        proj = _projection_with_army()
        pending = PendingRankBonusChoice(
            pending_id=(1, 0),
            instruction='Choose',
            options=[Admin()],
            level=1,
            continue_career_progress=False,
        )
        event = pending.event_from_form({'skill': Admin(level=Level(value=1)).model_dump_json()})

        pending.on_skill_chosen(proj, event)

        assert proj.summary.skill_level(Admin, 0) == 1
        assert proj.pending_inputs == ()


class TestQueueReenlistOrAging:
    def test_prisoner_freed_without_aging_sets_up_muster_out(self):
        from ceres.character.domain.career.muster_out import PendingMusterOut

        proj = _projection_with_army(age=22)
        proj.prisoner_freed = True

        queue_reenlist_or_aging(proj, event_id=16, idx=0)

        assert proj.prisoner_freed is False
        assert any(isinstance(p, PendingMusterOut) for p in proj.pending_inputs)

    def test_prisoner_freed_with_aging_marks_muster_out_pending_setup(self):
        proj = _projection_with_army(age=30)
        proj.prisoner_freed = True

        queue_reenlist_or_aging(proj, event_id=16, idx=0)

        assert proj.pending_reenlist is False
        assert proj.summary.career_terms[-1].require_muster_out().pending_setup is True

    def test_forced_leave_without_aging_sets_up_muster_out(self):
        from ceres.character.domain.career.muster_out import PendingMusterOut

        proj = _projection_with_army(age=22)
        proj.summary.career_terms[-1].forced_leave = True

        queue_reenlist_or_aging(proj, event_id=16, idx=0)

        assert any(isinstance(p, PendingMusterOut) for p in proj.pending_inputs)

    def test_forced_leave_with_aging_marks_muster_out_pending_setup(self):
        proj = _projection_with_army(age=30)
        proj.summary.career_terms[-1].forced_leave = True

        queue_reenlist_or_aging(proj, event_id=16, idx=0)

        assert proj.pending_reenlist is False
        assert proj.summary.career_terms[-1].require_muster_out().pending_setup is True

    def test_forced_stay_removes_muster_out_from_assignment_change_choice(self):
        proj = _projection_with_army(age=22)
        proj.summary.career_terms[-1].forced_stay = True

        queue_reenlist_or_aging(proj, event_id=16, idx=0)

        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingAssignmentChangeChoice))
        assert pending.muster_out is False


class TestPurgeCareerPendings:
    def test_removes_survive_pending(self):
        proj = _projection()
        proj.queue_deferred(PendingSurvive(pending_id=(1, 0), instruction='Roll'))
        purge_career_pendings(proj)
        assert not any(isinstance(p, PendingSurvive) for p in proj.pending_inputs)

    def test_preserves_non_career_pendings(self):
        from ceres.character.domain.characteristics import ConnectionKind
        from ceres.character.domain.connection_events import PendingConnectionName

        proj = _projection()
        conn = PendingConnectionName(
            pending_id='conn_0',
            connection_index=0,
            connection_kind=ConnectionKind.ALLY,
            note_prefill='',
            instruction='Name ally',
        )
        proj.queue_deferred(PendingSurvive(pending_id=(1, 0), instruction='Roll'))
        proj.queue_deferred(conn)
        purge_career_pendings(proj)
        assert conn in proj.pending_inputs

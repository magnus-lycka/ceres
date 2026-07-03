"""Unit tests for career_events pending input mechanics."""

from ceres.character.domain.career import ARMY
from ceres.character.domain.career.career_data import SkillTableOption
from ceres.character.domain.career.career_events import (
    AssignmentChangeChoiceHandler,
    MishapHandler,
    PendingAssignmentChangeChoice,
    PendingMishap,
    PendingReenlist,
    PendingSkillTable,
    PendingSurvive,
    PendingSwitchAssignment,
    PendingTermEvent,
    ReenlistHandler,
    SkillTableHandler,
    SurviveHandler,
    SwitchAssignmentHandler,
    TermEventHandler,
    _apply_skill_table_entry,
    purge_career_pendings,
)
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Admin
from ceres.character.domain.sophont import VILANI
from ceres.character.input_specs import NumberEntry, Select
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD


def _projection(**kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, **kwargs),
    )


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
        proj.pending_inputs.append(survive)

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
        proj.pending_inputs.append(survive)

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


class TestPurgeCareerPendings:
    def test_removes_survive_pending(self):
        proj = _projection()
        proj.pending_inputs.append(PendingSurvive(pending_id=(1, 0), instruction='Roll'))
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
        proj.pending_inputs.append(PendingSurvive(pending_id=(1, 0), instruction='Roll'))
        proj.pending_inputs.append(conn)
        purge_career_pendings(proj)
        assert conn in proj.pending_inputs


class TestApplySkillTableEntry:
    def test_increments_characteristic(self):
        proj = _projection(characteristics={Chars.STR: 7})
        _apply_skill_table_entry(proj, Chars.STR)
        assert proj.summary.characteristics[Chars.STR] == 8

    def test_increments_missing_characteristic_from_zero(self):
        proj = _projection()
        _apply_skill_table_entry(proj, Chars.EDU)
        assert proj.summary.characteristics[Chars.EDU] == 1

    def test_increments_skill(self):
        proj = _projection()
        _apply_skill_table_entry(proj, Admin())
        assert proj.summary.skill_level(Admin, 0) == 1

    def test_increments_possessed_psi_talent(self):
        from ceres.character.domain.psionics_data import Psi, Psionics, Telepathy

        proj = _projection()
        proj.summary.psionics = Psionics(psionic_talent_skills=[Telepathy()])
        _apply_skill_table_entry(proj, Psi(root=Telepathy()))
        assert proj.summary.psionics.talent_level(Telepathy) == 1

    def test_no_op_for_unpossessed_psi_talent(self):
        from ceres.character.domain.psionics_data import Clairvoyance, Psi, Psionics, Telepathy

        proj = _projection()
        proj.summary.psionics = Psionics(psionic_talent_skills=[Clairvoyance()])
        _apply_skill_table_entry(proj, Psi(root=Telepathy()))
        assert proj.summary.psionics.talent_level(Telepathy) is None
        assert proj.summary.psionics.talent_level(Clairvoyance) == 0

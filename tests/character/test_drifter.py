"""Tests for the Drifter career — barbarian, wanderer, and scavenger assignments."""

from ceres.character.domain.career import DRIFTER
from ceres.character.domain.career.career_events import (
    CareerChoiceHandler,
    CareerEntryHandler,
    MishapHandler,
    PendingAdvancement,
    PendingCareerChoice,
    PendingChoices,
    PendingInitialTrainingChoice,
    PendingMusterOut,
    PendingSkillChoice,
    PendingSurvive,
    SkillChoiceHandler,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.drifter import (
    DrifterEvent3Accept,
    DrifterEvent3Decline,
    DrifterEvent9Accept,
    DrifterEvent9Decline,
    DrifterEvent9Injury,
    DrifterEvent9Prison,
    PendingDrifterEvent8SkillRoll,
    PendingDrifterEvent9RollSkillRoll,
    PendingDrifterMishap5SkillRoll,
)
from ceres.character.domain.career.loader import load_careers, selectable_careers
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.connection import (
    Enemy,
    Rival,
)
from ceres.character.domain.health.health_events import PendingInjuryTable
from ceres.character.domain.skills import Admin, Athletics, Carouse, Deception, Drive, GunCombat, Level, Melee, Survival
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD, CharacterDriver


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — END DM+0."""
    started = Event(handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Boss'))
    ucp = Event(fulfills=(started.id, 0), handler=UcpHandler(ucp='7869A5'))
    background = Event(
        fulfills=(ucp.id, 0),
        handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()]),
    )
    return [started, ucp, background]


def _enter_drifter(assignment: str = 'Wanderer', qual_roll: int = 1) -> list:
    """Through qualification — END 0+, always passes."""
    base = _setup()
    entry = Event(
        fulfills=(base[-1].id, 0),
        handler=CareerEntryHandler(
            career=DRIFTER, assignment=DRIFTER.assignment(assignment), qualification_roll=qual_roll
        ),
    )
    return [
        *base,
        entry,
    ]


def _through_survive(assignment: str = 'Wanderer', survive_roll: int = 7) -> list:
    """Through survival — Wanderer END 7+, END=6 DM+0, roll 7 → 7 ≥ 7 (pass)."""
    base = _enter_drifter(assignment)
    return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int, assignment: str = 'Wanderer') -> list:
    base = _through_survive(assignment)
    return [*base, Event(fulfills=(base[-1].id, 0), handler=TermEventHandler(roll=event_roll))]


# ── basic career entry ────────────────────────────────────────────────────────


def test_drifter_career_loads_and_is_selectable():
    drifter = load_careers()['Drifter']

    assert 'Drifter' in selectable_careers()
    assert [assignment.name for assignment in drifter.assignments] == ['Barbarian', 'Wanderer', 'Scavenger']


def test_drifter_first_career_basic_training_uses_assignment_skills():
    base = _setup()
    events = [
        *base,
        Event(
            fulfills=(base[-1].id, 0),
            handler=CareerEntryHandler(career=DRIFTER, assignment=DRIFTER.assignment('Wanderer'), qualification_roll=0),
        ),
    ]

    projection = replay(1, events)

    assert projection.summary.skill_level(Deception) == 0
    assert projection.summary.skill_level(Survival) == 0
    assert projection.summary.skill_level(Melee) is None


def test_drifter_basic_training_defers_survival_for_assignment_skill_choices():
    base = _setup()
    events = [
        *base,
        Event(
            fulfills=(base[-1].id, 0),
            handler=CareerEntryHandler(
                career=DRIFTER, assignment=DRIFTER.assignment('Scavenger'), qualification_roll=0
            ),
        ),
    ]

    projection = replay(1, events)

    assert any(isinstance(p, PendingInitialTrainingChoice) for p in projection.pending_inputs)
    assert not any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


# ── mishap 5: betrayed by a friend ───────────────────────────────────────────


class TestDrifterMishap5:
    def _setup_to_mishap(self) -> list:
        base = _enter_drifter('Wanderer')
        return [*base, Event(fulfills=(base[-1].id, 0), handler=SurviveHandler(roll=6))]

    def test_mishap_5_creates_2d_roll_pending(self):
        base = self._setup_to_mishap()
        events = [*base, Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingDrifterMishap5SkillRoll)), None)
        assert pending is not None
        assert pending.options == []

    def test_mishap_5_adds_rival_on_any_roll(self):
        for roll in (2, 7):
            base = self._setup_to_mishap()
            mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
            events = [
                *base,
                mishap,
                Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=roll)),
            ]
            projection = replay(1, events)
            rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
            assert len(rivals) == 1, f'roll={roll}'

    def test_natural_2_forces_prisoner_as_next_career_choice(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=2)),
        ]
        projection = replay(1, events)
        # No muster-out rolls (lose_current_term=True, 1 term, rank 0), so forced_next_career
        # is consumed immediately into a PendingCareerChoice with options=['Prisoner']
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert [c.name for c in pending.options] == ['Prisoner']

    def test_other_rolls_allow_free_career_choice(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert 'Prisoner' not in {c.name for c in pending.options}

    def test_mishap_5_ends_career(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_mishap_5_loses_muster_out(self):
        base = self._setup_to_mishap()
        mishap = Event(fulfills=(base[-1].id, 0), handler=MishapHandler(roll=5))
        events = [
            *base,
            mishap,
            Event(fulfills=(mishap.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── event 3: patron job offer ─────────────────────────────────────────────────


class TestDrifterEvent3:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=3)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {DrifterEvent3Accept, DrifterEvent3Decline}

    def test_accept_schedules_qualification_dm_4(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=DrifterEvent3Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.pending_qualification_dm == 4

    def test_decline_no_qualification_dm(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=DrifterEvent3Decline.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.pending_qualification_dm == 0

    def test_both_choices_queue_advancement(self):
        for choice_cls in (DrifterEvent3Accept, DrifterEvent3Decline):
            base = self._setup_to_event()
            events = [
                *base,
                Event(
                    fulfills=(base[-1].id, 0),
                    handler=CareerChoiceHandler(choice=choice_cls.model_fields['kind'].default),
                ),
            ]
            projection = replay(1, events)
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs), choice_cls


# ── event 8: attacked by enemies ─────────────────────────────────────────────


class TestDrifterEvent8:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=8)

    def test_creates_enemy_immediately(self):
        projection = replay(1, self._setup_to_event())
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_creates_skill_roll_pending_with_melee_or_gun_combat(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingDrifterEvent8SkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == [Melee(), GunCombat()]

    def test_success_creates_skill_choice(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert pending.options == [Melee(), GunCombat()]

    def test_failure_adds_injury_problem(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=5)),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() for p in projection.summary.problems)

    def test_failure_queues_advancement(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=5)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 9: risky adventure ──────────────────────────────────────────────────


class TestDrifterEvent9:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=9)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {DrifterEvent9Accept, DrifterEvent9Decline}

    def test_decline_queues_advancement(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=DrifterEvent9Decline.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_1d_roll_pending(self):
        base = self._setup_to_event()
        events = [
            *base,
            Event(
                fulfills=(base[-1].id, 0),
                handler=CareerChoiceHandler(choice=DrifterEvent9Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingDrifterEvent9RollSkillRoll)), None)
        assert pending is not None
        assert pending.options == []

    def test_1d_roll_low_creates_injury_or_prison_choice(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=DrifterEvent9Accept.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=1)),
        ]
        projection = replay(1, events)
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {DrifterEvent9Injury, DrifterEvent9Prison}

    def test_1d_roll_low_also_queues_advancement(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=DrifterEvent9Accept.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=2)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_injury_choice_creates_injury_table_pending(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=DrifterEvent9Accept.model_fields['kind'].default),
        )
        roll_event = Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=1))
        events = [
            *base,
            choice,
            roll_event,
            Event(
                fulfills=(roll_event.id, 0),
                handler=CareerChoiceHandler(choice=DrifterEvent9Injury.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_prison_choice_forces_prisoner_next_career(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=DrifterEvent9Accept.model_fields['kind'].default),
        )
        roll_event = Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=2))
        events = [
            *base,
            choice,
            roll_event,
            Event(
                fulfills=(roll_event.id, 0),
                handler=CareerChoiceHandler(choice=DrifterEvent9Prison.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert projection.forced_next_career is not None
        assert projection.forced_next_career.name == 'Prisoner'

    def test_1d_roll_3_creates_injury_table(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=DrifterEvent9Accept.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=3)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_1d_roll_high_schedules_extra_benefit_roll(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=DrifterEvent9Accept.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=5)),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_1d_roll_high_queues_advancement(self):
        base = self._setup_to_event()
        choice = Event(
            fulfills=(base[-1].id, 0),
            handler=CareerChoiceHandler(choice=DrifterEvent9Accept.model_fields['kind'].default),
        )
        events = [
            *base,
            choice,
            Event(fulfills=(choice.id, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=4)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 10: honed abilities ────────────────────────────────────────────────


class TestDrifterEvent10:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=10)

    def test_presents_existing_skills_as_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        option_types = {type(o) for o in pending.options}
        current_skill_types = {type(s) for s in projection.summary.skills}
        assert option_types == current_skill_types

    def test_chosen_skill_is_incremented(self):
        # Admin starts at 0 from background skills; choosing it at level 1 should increment it
        base = self._setup_to_event()
        events = [
            *base,
            Event(fulfills=(base[-1].id, 0), handler=SkillChoiceHandler(skill=Admin(level=Level(value=1)))),
        ]
        projection = replay(1, events)
        assert projection.summary.skill_level(Admin) == 1


# ── event 11: forcibly drafted ────────────────────────────────────────────────


class TestDrifterEvent11:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=11)

    def test_adds_problem_note_about_draft(self):
        projection = replay(1, self._setup_to_event())
        assert any('draft' in p.lower() or 'Draft' in p for p in projection.summary.problems)

    def test_queues_advancement(self):
        projection = replay(1, self._setup_to_event())
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── mishap 1: severely injured ────────────────────────────────────────────────


class TestDrifterMishap1:
    def test_uses_common_handler(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Drifter', 'Wanderer', roll=1)
        d.survive(2)
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}

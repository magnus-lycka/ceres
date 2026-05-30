"""Tests for the Drifter career — barbarian, wanderer, and scavenger assignments."""

from ceres.character.careers.loader import load_careers, selectable_careers
from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    SkillRollEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.projection import (
    Enemy,
    PendingAdvancement,
    PendingCareerChoice,
    PendingCareerEvent,
    PendingCareerSkillRoll,
    PendingInitialTrainingChoice,
    PendingInjuryTable,
    PendingMusterOut,
    PendingSkillChoice,
    PendingSurvive,
    Rival,
)
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — END DM+0."""
    return [
        CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Boss'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _enter_drifter(assignment: str = 'Wanderer', qual_roll: int = 1) -> list:
    """Through qualification — END 0+, always passes."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Drifter', assignment=assignment, qualification_roll=qual_roll),
    ]


def _through_survive(assignment: str = 'Wanderer', survive_roll: int = 7) -> list:
    """Through survival — Wanderer END 7+, END=6 DM+0, roll 7 → 7 ≥ 7 (pass)."""
    return [*_enter_drifter(assignment), SurviveEvent(id=5, fulfills='4.0', roll=survive_roll)]


def _through_term_event(event_roll: int, assignment: str = 'Wanderer') -> list:
    return [*_through_survive(assignment), TermEventEvent(id=6, fulfills='5.0', roll=event_roll)]


# ── basic career entry ────────────────────────────────────────────────────────


def test_drifter_career_loads_and_is_selectable():
    drifter = load_careers()['Drifter']

    assert 'Drifter' in selectable_careers()
    assert [assignment.name for assignment in drifter.assignments] == ['Barbarian', 'Wanderer', 'Scavenger']


def test_drifter_first_career_basic_training_uses_assignment_skills():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Drifter', assignment='Wanderer', qualification_roll=0),
    ]

    projection = replay(1, events)

    assert projection.summary.skill_level('Deception') == 0
    assert projection.summary.skill_level('Survival') == 0
    assert projection.summary.skill_level('Melee') is None


def test_drifter_basic_training_defers_survival_for_assignment_skill_choices():
    events = [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Drifter', assignment='Scavenger', qualification_roll=0),
    ]

    projection = replay(1, events)

    assert any(isinstance(p, PendingInitialTrainingChoice) for p in projection.pending_inputs)
    assert not any(isinstance(p, PendingSurvive) for p in projection.pending_inputs)


# ── mishap 5: betrayed by a friend ───────────────────────────────────────────


class TestDrifterMishap5:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_drifter('Wanderer'),
            SurviveEvent(id=5, fulfills='4.0', roll=6),  # END 7+, DM+0, 6 < 7 — fail
        ]

    def test_mishap_5_creates_2d_roll_pending(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=5)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None
        assert pending.roll == 5
        assert pending.options == []

    def test_mishap_5_adds_rival_on_any_roll(self):
        for roll in (2, 7):
            events = [
                *self._setup_to_mishap(),
                MishapEvent(id=6, fulfills='5.0', roll=5),
                SkillRollEvent(id=7, fulfills='6.0', context='drifter_mishap_5', skill=Admin(), modified_roll=roll),
            ]
            projection = replay(1, events)
            rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
            assert len(rivals) == 1, f'roll={roll}'

    def test_natural_2_forces_prisoner_as_next_career_choice(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillRollEvent(id=7, fulfills='6.0', context='drifter_mishap_5', skill=Admin(), modified_roll=2),
        ]
        projection = replay(1, events)
        # No muster-out rolls (lose_current_term=True, 1 term, rank 0), so forced_next_career
        # is consumed immediately into a PendingCareerChoice with options=['Prisoner']
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert pending.options == ['Prisoner']

    def test_other_rolls_allow_free_career_choice(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillRollEvent(id=7, fulfills='6.0', context='drifter_mishap_5', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerChoice)), None)
        assert pending is not None
        assert 'Prisoner' not in pending.options

    def test_mishap_5_ends_career(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillRollEvent(id=7, fulfills='6.0', context='drifter_mishap_5', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None

    def test_mishap_5_loses_muster_out(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=5),
            SkillRollEvent(id=7, fulfills='6.0', context='drifter_mishap_5', skill=Admin(), modified_roll=7),
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
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 3),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'accept', 'decline'}

    def test_accept_schedules_qualification_dm_4(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_3', choice='accept'),
        ]
        projection = replay(1, events)
        qual_effects = [se for se in projection.scheduled_effects if se.trigger == 'qualification']
        assert any(se.effect.get('amount') == 4 for se in qual_effects)

    def test_decline_no_qualification_dm(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_3', choice='decline'),
        ]
        projection = replay(1, events)
        qual_effects = [se for se in projection.scheduled_effects if se.trigger == 'qualification']
        assert len(qual_effects) == 0

    def test_both_choices_queue_advancement(self):
        for choice in ('accept', 'decline'):
            events = [
                *self._setup_to_event(),
                CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_3', choice=choice),
            ]
            projection = replay(1, events)
            assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs), choice


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
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 8),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'Melee', 'Gun Combat'}

    def test_success_creates_skill_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='drifter_event_8', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert set(pending.options) == {'Melee', 'Gun Combat'}

    def test_failure_adds_injury_problem(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='drifter_event_8', skill=Admin(), modified_roll=5),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() for p in projection.summary.problems)

    def test_failure_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='drifter_event_8', skill=Admin(), modified_roll=5),
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
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 9),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'accept', 'decline'}

    def test_decline_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_9', choice='decline'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_1d_roll_pending(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_9', choice='accept'),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None
        assert pending.options == []

    def test_1d_roll_low_creates_injury_or_prison_choice(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_9', choice='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='drifter_event_9_roll', skill=Admin(), modified_roll=1),
        ]
        projection = replay(1, events)
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 9),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'injury', 'prison'}

    def test_1d_roll_low_also_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_9', choice='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='drifter_event_9_roll', skill=Admin(), modified_roll=2),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_injury_choice_creates_injury_table_pending(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_9', choice='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='drifter_event_9_roll', skill=Admin(), modified_roll=1),
            CareerChoiceEvent(id=9, fulfills='8.0', context='drifter_event_9', choice='injury'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_prison_choice_forces_prisoner_next_career(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_9', choice='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='drifter_event_9_roll', skill=Admin(), modified_roll=2),
            CareerChoiceEvent(id=9, fulfills='8.0', context='drifter_event_9', choice='prison'),
        ]
        projection = replay(1, events)
        assert projection.forced_next_career == 'Prisoner'

    def test_1d_roll_3_creates_injury_table(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_9', choice='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='drifter_event_9_roll', skill=Admin(), modified_roll=3),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingInjuryTable) for p in projection.pending_inputs)

    def test_1d_roll_high_schedules_extra_benefit_roll(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_9', choice='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='drifter_event_9_roll', skill=Admin(), modified_roll=5),
        ]
        projection = replay(1, events)
        add_effects = [se for se in projection.scheduled_effects if se.trigger == 'muster_out_add']
        assert len(add_effects) == 1

    def test_1d_roll_high_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='drifter_event_9', choice='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='drifter_event_9_roll', skill=Admin(), modified_roll=4),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


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

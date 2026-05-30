"""Tests for the Navy career — line/crew, engineer/gunner, and flight assignments."""

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
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    PendingCommissionChoice,
    PendingMusterOut,
    PendingSkillChoice,
)
from ceres.character.replay import replay
from ceres.character.skills import Admin, Athletics, Carouse, Drive


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — INT DM+1, EDU DM+2."""
    return [
        CharacterStartedEvent(id=1, sophont='Vilani', player='NPC', name='Ens'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _enter_navy(assignment: str = 'Line/Crew', qual_roll: int = 5) -> list:
    """Through qualification — INT 6+, INT=9 DM+1, roll 5 → 6 ≥ 6."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Navy', assignment=assignment, qualification_roll=qual_roll),
    ]


def _through_survive(assignment: str = 'Line/Crew', survive_roll: int = 4) -> list:
    """Navy service skills are all single-choice — survival queued at '4.0'.

    Line/Crew survival: INT 5+, DM+1, roll 4 → 5 ≥ 5 (pass).
    """
    return [*_enter_navy(assignment), SurviveEvent(id=5, fulfills='4.0', roll=survive_roll)]


def _through_term_event(event_roll: int, assignment: str = 'Line/Crew') -> list:
    return [*_through_survive(assignment), TermEventEvent(id=6, fulfills='5.0', roll=event_roll)]


# ── mishap 3: battle skill check (assignment-specific) ───────────────────────


class TestNavyMishap3:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_navy('Line/Crew'),
            SurviveEvent(id=5, fulfills='4.0', roll=3),  # INT 5+, DM+1, 3 → 4 < 5 — fail
        ]

    def test_line_crew_mishap_3_options_are_electronics_or_gunner(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=3)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None
        assert set(pending.options) == {'Electronics', 'Gunner'}

    def test_engineer_gunner_mishap_3_options_are_mechanic_or_vacc_suit(self):
        events = [
            *_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Navy', assignment='Engineer/Gunner', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=4),  # INT 6+, DM+1, fail with roll 4
            MishapEvent(id=6, fulfills='5.0', roll=3),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None
        assert set(pending.options) == {'Mechanic', 'Vacc Suit'}

    def test_flight_mishap_3_options_are_pilot_or_tactics(self):
        events = [
            *_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Navy', assignment='Flight', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=6),  # DEX 7+, DM+1, fail with roll 6 → 7 ≥ 7 — pass, need fail
            # Actually DEX 7+, DEX=8, DM+1, need roll 6+ to pass; roll 5 → 6 < 7 fails
        ]
        # Reset: Flight survival DEX 7+, DEX=8, DM+1, roll 5 → 6 < 7 — fail
        events = [
            *_setup(),
            CareerEvent(id=4, fulfills='3.0', career='Navy', assignment='Flight', qualification_roll=5),
            SurviveEvent(id=5, fulfills='4.0', roll=5),  # DEX 7+, DM+1, 5 → 6 < 7 — fail
            MishapEvent(id=6, fulfills='5.0', roll=3),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None
        assert set(pending.options) == {'Pilot', 'Tactics'}

    def test_success_keeps_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=3),
            SkillRollEvent(id=7, fulfills='6.0', context='navy_mishap_3', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_failure_loses_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=3),
            SkillRollEvent(id=7, fulfills='6.0', context='navy_mishap_3', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_both_outcomes_end_career(self):
        for roll in (9, 7):
            events = [
                *self._setup_to_mishap(),
                MishapEvent(id=6, fulfills='5.0', roll=3),
                SkillRollEvent(id=7, fulfills='6.0', context='navy_mishap_3', skill=Admin(), modified_roll=roll),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None, f'roll={roll}'


# ── mishap 4: blamed for accident ────────────────────────────────────────────


class TestNavyMishap4:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_navy('Line/Crew'),
            SurviveEvent(id=5, fulfills='4.0', roll=3),
        ]

    def test_mishap_4_creates_choice_pending(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=4)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerMishap)), None)
        assert pending is not None
        assert set(pending.options) == {'responsible', 'not_responsible'}

    def test_responsible_adds_problem_note(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent(id=7, fulfills='6.0', context='navy_mishap_4', choice='responsible'),
        ]
        projection = replay(1, events)
        assert any('free' in p.lower() or 'skill' in p.lower() for p in projection.summary.problems)

    def test_responsible_loses_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent(id=7, fulfills='6.0', context='navy_mishap_4', choice='responsible'),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_not_responsible_adds_enemy(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent(id=7, fulfills='6.0', context='navy_mishap_4', choice='not_responsible'),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_not_responsible_keeps_benefit_roll(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent(id=7, fulfills='6.0', context='navy_mishap_4', choice='not_responsible'),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_both_choices_end_career(self):
        for choice in ('responsible', 'not_responsible'):
            events = [
                *self._setup_to_mishap(),
                MishapEvent(id=6, fulfills='5.0', roll=4),
                CareerChoiceEvent(id=7, fulfills='6.0', context='navy_mishap_4', choice=choice),
            ]
            projection = replay(1, events)
            assert projection.summary.current_career is None, choice


# ── event 5: advanced training ────────────────────────────────────────────────


class TestNavyEvent5:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=5)

    def test_creates_edu_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 5),
            None,
        )
        assert pending is not None
        assert pending.options == ['EDU']

    def test_success_creates_skill_choice_from_existing_skills(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='navy_event_5', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        # Navy service skills auto-applied first career: Pilot, Vacc Suit, Athletics, Gunner, Mechanic, Gun Combat
        assert 'Athletics' in pending.options

    def test_failure_no_skill_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='navy_event_5', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_queues_career_progress(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='navy_event_5', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        # On failure no skill choice created; _apply_skill_roll auto-queues advancement
        # (Navy at rank 0 can attempt commission, so may be PendingCommissionChoice)
        has_progress = any(
            isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs
        )
        assert has_progress


# ── event 10: abuse position for profit ──────────────────────────────────────


class TestNavyEvent10:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=10)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 10),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'profit', 'refuse'}

    def test_profit_schedules_extra_benefit_roll(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='navy_event_10', choice='profit'),
        ]
        projection = replay(1, events)
        add_effects = [se for se in projection.scheduled_effects if se.trigger == 'muster_out_add']
        assert len(add_effects) == 1

    def test_refuse_schedules_advancement_dm_2(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='navy_event_10', choice='refuse'),
        ]
        projection = replay(1, events)
        dm_effects = [se for se in projection.scheduled_effects if se.trigger == 'advancement']
        assert any(se.effect.get('amount') == 2 for se in dm_effects)

    def test_profit_no_advancement_dm(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='navy_event_10', choice='profit'),
        ]
        projection = replay(1, events)
        dm_effects = [se for se in projection.scheduled_effects if se.trigger == 'advancement']
        assert len(dm_effects) == 0

    def test_both_choices_queue_career_progress(self):
        for choice in ('profit', 'refuse'):
            events = [
                *self._setup_to_event(),
                CareerChoiceEvent(id=7, fulfills='6.0', context='navy_event_10', choice=choice),
            ]
            projection = replay(1, events)
            # Navy at rank 0 can attempt commission → PendingCommissionChoice; otherwise PendingAdvancement
            has_progress = any(
                isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs
            )
            assert has_progress, choice

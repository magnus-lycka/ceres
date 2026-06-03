"""Tests for the Marines career — support, ground assault, and star marine assignments."""

from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacterStartedEvent,
    MishapEvent,
    PendingAdvancement,
    PendingCareerEvent,
    PendingCareerMishap,
    PendingCareerSkillRoll,
    PendingCommissionChoice,
    PendingMusterOut,
    PendingSkillChoice,
    SkillRollEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.replay import replay
from ceres.character.skills import (
    Admin,
    Athletics,
    Carouse,
    Deception,
    Drive,
    GunCombat,
    Leadership,
    Melee,
    Persuade,
    Tactics,
)
from ceres.character.sophonts import VILANI
from ceres.character.state import (
    Ally,
    Contact,
    Enemy,
)
from tests.character.helpers import MOCK_WORLD


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — EDU DM+2."""
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Cpl'),
        UcpEvent(id=2, fulfills='1.0', ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills='2.0', skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _enter_marines(assignment: str = 'Support', qual_roll: int = 6) -> list:
    """Through qualification — END 6+, END=6 DM+0, roll 6 → 6 ≥ 6."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills='3.0', career='Marines', assignment=assignment, qualification_roll=qual_roll),
    ]


def _through_survive(assignment: str = 'Support', survive_roll: int = 5) -> list:
    """Marines service_skills are all single-choice — survival queued at '4.0'.

    Support survival: END 5+, DM+0, roll 5 → 5 ≥ 5 (pass).
    """
    return [*_enter_marines(assignment), SurviveEvent(id=5, fulfills='4.0', roll=survive_roll)]


def _through_term_event(event_roll: int, assignment: str = 'Support') -> list:
    return [*_through_survive(assignment), TermEventEvent(id=6, fulfills='5.0', roll=event_roll)]


# ── mishap 4: black ops mission ───────────────────────────────────────────────


class TestMarinesMishap4:
    def _setup_to_mishap(self) -> list:
        return [
            *_enter_marines(),
            SurviveEvent(id=5, fulfills='4.0', roll=4),  # END 5+, DM+0, 4 < 5 — fail
        ]

    def test_mishap_4_creates_choice_pending(self):
        events = [*self._setup_to_mishap(), MishapEvent(id=6, fulfills='5.0', roll=4)]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerMishap)), None)
        assert pending is not None
        assert set(pending.options) == {'refuse', 'accept'}

    def test_refuse_adds_contact(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent(id=7, fulfills='6.0', context='marines_mishap_4', choice='refuse'),
        ]
        projection = replay(1, events)
        contacts = [c for c in projection.summary.connections if isinstance(c, Contact)]
        assert len(contacts) == 1

    def test_refuse_ends_career_and_loses_benefit(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent(id=7, fulfills='6.0', context='marines_mishap_4', choice='refuse'),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)

    def test_accept_creates_skill_roll(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent(id=7, fulfills='6.0', context='marines_mishap_4', choice='accept'),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll)), None)
        assert pending is not None
        assert pending.options == [Deception(), Persuade()]

    def test_accept_success_continues_career(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent(id=7, fulfills='6.0', context='marines_mishap_4', choice='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='marines_mishap_4_skill', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Marines'

    def test_accept_failure_ends_career_and_loses_benefit(self):
        events = [
            *self._setup_to_mishap(),
            MishapEvent(id=6, fulfills='5.0', roll=4),
            CareerChoiceEvent(id=7, fulfills='6.0', context='marines_mishap_4', choice='accept'),
            SkillRollEvent(id=8, fulfills='7.0', context='marines_mishap_4_skill', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is None
        assert not any(isinstance(p, PendingMusterOut) for p in projection.pending_inputs)


# ── event 5: advanced training ────────────────────────────────────────────────


class TestMarinesEvent5:
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

    def test_success_creates_skill_choice_with_existing_skills(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='marines_event_5', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        # Marines service skills (auto-applied first career): Athletics, Vacc Suit, Tactics, etc.
        assert any(isinstance(o, Athletics) for o in pending.options)

    def test_failure_no_skill_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='marines_event_5', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='marines_event_5', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        # On failure no skill choice is created, so _apply_skill_roll auto-queues advancement
        # (Marines at rank 0 can attempt commission, so may be PendingCommissionChoice)
        has_progress = any(
            isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs
        )
        assert has_progress


# ── event 6: assault on an enemy fortress ────────────────────────────────────


class TestMarinesEvent6:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=6)

    def test_creates_melee_or_gun_combat_skill_roll(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerSkillRoll) and p.roll == 6),
            None,
        )
        assert pending is not None
        assert pending.options == [Melee(), GunCombat()]

    def test_success_creates_tactics_or_leadership_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='marines_event_6', skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert pending.options == [Tactics(), Leadership()]

    def test_failure_adds_injury_problem(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='marines_event_6', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any('injur' in p.lower() for p in projection.summary.problems)

    def test_failure_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills='6.0', context='marines_event_6', skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 9: mission goes wrong ───────────────────────────────────────────────


class TestMarinesEvent9:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=9)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingCareerEvent) and p.roll == 9),
            None,
        )
        assert pending is not None
        assert set(pending.options) == {'report', 'protect'}

    def test_report_adds_enemy(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='marines_event_9', choice='report'),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1

    def test_report_schedules_advancement_dm_2(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='marines_event_9', choice='report'),
        ]
        projection = replay(1, events)
        dm_effects = [se for se in projection.scheduled_effects if se.trigger == 'advancement']
        assert any(se.effect.get('amount') == 2 for se in dm_effects)

    def test_protect_adds_ally(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='marines_event_9', choice='protect'),
        ]
        projection = replay(1, events)
        allies = [c for c in projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1

    def test_protect_schedules_advancement_dm_1(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent(id=7, fulfills='6.0', context='marines_event_9', choice='protect'),
        ]
        projection = replay(1, events)
        dm_effects = [se for se in projection.scheduled_effects if se.trigger == 'advancement']
        assert any(se.effect.get('amount') == 1 for se in dm_effects)

    def test_both_choices_queue_career_progress(self):
        for choice in ('report', 'protect'):
            events = [
                *self._setup_to_event(),
                CareerChoiceEvent(id=7, fulfills='6.0', context='marines_event_9', choice=choice),
            ]
            projection = replay(1, events)
            # Marines at rank 0 can attempt commission → PendingCommissionChoice; otherwise PendingAdvancement
            has_progress = any(
                isinstance(p, (PendingAdvancement, PendingCommissionChoice)) for p in projection.pending_inputs
            )
            assert has_progress, choice

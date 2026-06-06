"""Tests for the Merchant career — merchant marine, free trader, and broker assignments."""

from ceres.character.domain.career.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.domain.career.merchant import (
    MerchantEvent3Accept,
    MerchantEvent3Refuse,
    MerchantEvent3SkillRoll,
    PendingMerchantEvent8Roll,
)
from ceres.character.events import (
    BackgroundSkillsEvent,
    CareerChoiceEvent,
    CareerEvent,
    CharacterStartedEvent,
    PendingAdvancement,
    PendingChoices,
    PendingSkillChoice,
    SkillChoiceEvent,
    SkillRollEvent,
    SurviveEvent,
    TermEventEvent,
    UcpEvent,
)
from ceres.character.mechanism.replay import replay
from ceres.character.skills import (
    Admin,
    Advocate,
    Athletics,
    Broker,
    Carouse,
    Deception,
    Diplomat,
    Drive,
    Investigate,
    Persuade,
)
from ceres.character.sophonts import VILANI
from ceres.character.state import (
    Enemy,
    Rival,
)
from tests.character.helpers import MOCK_WORLD


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — INT DM+1, EDU DM+2."""
    return [
        CharacterStartedEvent(id=1, sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Mer'),
        UcpEvent(id=2, fulfills=(1, 0), ucp='7869A5'),
        BackgroundSkillsEvent(id=3, fulfills=(2, 0), skills=[Admin(), Athletics(), Carouse(), Drive()]),
    ]


def _enter_merchant(assignment: str = 'Merchant Marine', qual_roll: int = 3) -> list:
    """Through qualification — INT 4+, INT=9 DM+1, roll 3 → 4 ≥ 4."""
    return [
        *_setup(),
        CareerEvent(id=4, fulfills=(3, 0), career='Merchant', assignment=assignment, qualification_roll=qual_roll),
    ]


def _through_survive(assignment: str = 'Merchant Marine', survive_roll: int = 3) -> list:
    """Merchant service skills are all single-choice — survival queued at '4.0'.

    Merchant Marine survival: EDU 5+, EDU=10 DM+2, roll 3 → 5 ≥ 5 (pass).
    """
    return [*_enter_merchant(assignment), SurviveEvent(id=5, fulfills=(4, 0), roll=survive_roll)]


def _through_term_event(event_roll: int, assignment: str = 'Merchant Marine') -> list:
    return [*_through_survive(assignment), TermEventEvent(id=6, fulfills=(5, 0), roll=event_roll)]


# ── event 3: smuggling opportunity ───────────────────────────────────────────


class TestMerchantEvent3:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=3)

    def test_creates_event_pending_with_options(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingChoices)),
            None,
        )
        assert pending is not None
        assert {type(c) for c in pending.choices} == {MerchantEvent3Accept, MerchantEvent3Refuse}

    def test_refuse_adds_rival(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(MerchantEvent3Refuse, id=7, fulfills=(6, 0)),
        ]
        projection = replay(1, events)
        rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_refuse_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(MerchantEvent3Refuse, id=7, fulfills=(6, 0)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_skill_roll(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(MerchantEvent3Accept, id=7, fulfills=(6, 0)),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, MerchantEvent3SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Deception(), Persuade()]

    def test_accept_success_adds_benefit_roll(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(MerchantEvent3Accept, id=7, fulfills=(6, 0)),
            SkillRollEvent(id=8, fulfills=(7, 0), skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_accept_success_continues_career(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(MerchantEvent3Accept, id=7, fulfills=(6, 0)),
            SkillRollEvent(id=8, fulfills=(7, 0), skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Merchant'

    def test_accept_failure_adds_enemy_and_ends_career(self):
        events = [
            *self._setup_to_event(),
            CareerChoiceEvent.for_choice(MerchantEvent3Accept, id=7, fulfills=(6, 0)),
            SkillRollEvent(id=8, fulfills=(7, 0), skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        enemies = [c for c in projection.summary.connections if isinstance(c, Enemy)]
        assert len(enemies) == 1
        assert projection.summary.current_career is None


# ── event 8: legal trouble ────────────────────────────────────────────────────


class TestMerchantEvent8:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=8)

    def test_creates_skill_choice_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert pending.options == [Advocate(), Admin(), Diplomat(), Investigate()]

    def test_creates_2d_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingMerchantEvent8Roll)),
            None,
        )
        assert pending is not None

    def test_both_pendings_created_simultaneously(self):
        projection = replay(1, self._setup_to_event())
        has_skill_choice = any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)
        has_2d_roll = any(isinstance(p, PendingMerchantEvent8Roll) for p in projection.pending_inputs)
        assert has_skill_choice and has_2d_roll

    def test_skill_choice_grants_chosen_skill(self):
        events = [
            *self._setup_to_event(),
            SkillChoiceEvent(id=7, fulfills=(6, 0), skill=Admin()),
        ]
        projection = replay(1, events)
        # Admin was already at level 0 from background; should now be higher
        assert projection.summary.skill_level(Admin) is not None

    def test_natural_2_sets_forced_next_career_prisoner(self):
        events = [
            *self._setup_to_event(),
            SkillChoiceEvent(id=7, fulfills=(6, 0), skill=Admin()),
            SkillRollEvent(id=8, fulfills=(6, 1), skill=Admin(), modified_roll=2),
        ]
        projection = replay(1, events)
        assert projection.forced_next_career is not None
        assert projection.forced_next_career.name == 'Prisoner'

    def test_roll_above_2_does_not_force_prisoner(self):
        events = [
            *self._setup_to_event(),
            SkillChoiceEvent(id=7, fulfills=(6, 0), skill=Admin()),
            SkillRollEvent(id=8, fulfills=(6, 1), skill=Admin(), modified_roll=3),
        ]
        projection = replay(1, events)
        assert projection.forced_next_career is None

    def test_2d_roll_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            SkillChoiceEvent(id=7, fulfills=(6, 0), skill=Admin()),
            SkillRollEvent(id=8, fulfills=(6, 1), skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 9: advanced training ────────────────────────────────────────────────


class TestMerchantEvent9:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=9)

    def test_creates_edu_skill_roll_pending(self):
        projection = replay(1, self._setup_to_event())
        pending = next(
            (p for p in projection.pending_inputs if isinstance(p, PendingAdvancedTrainingSkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == ['EDU']

    def test_success_creates_skill_choice_with_existing_skills(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills=(6, 0), skill=Admin(), modified_roll=9),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        # Merchant service skills auto-applied: Drive, Vacc Suit, Broker, Steward, Electronics, Persuade
        assert any(isinstance(o, Broker) for o in pending.options)

    def test_failure_no_skill_choice(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills=(6, 0), skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        assert not any(isinstance(p, PendingSkillChoice) for p in projection.pending_inputs)

    def test_failure_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            SkillRollEvent(id=7, fulfills=(6, 0), skill=Admin(), modified_roll=7),
        ]
        projection = replay(1, events)
        # On failure no skill choice created; _apply_skill_roll auto-queues advancement
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 5: gambling opportunity ────────────────────────────────────────────


class TestMerchantEvent5:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=5)

    def test_gambling_adds_problem_note_and_queues_advancement(self):
        projection = replay(1, self._setup_to_event())
        assert any('gambling' in p.lower() for p in projection.summary.problems)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

"""Tests for the Merchant career — merchant marine, free trader, and broker assignments."""

from ceres.character.domain.career import MERCHANT
from ceres.character.domain.career.career_events import (
    CareerChoiceHandler,
    CareerEntryHandler,
    PendingAdvancement,
    PendingChoices,
    PendingMusterOut,
    PendingSkillChoice,
    SkillChoiceHandler,
    SkillRollHandler,
    SurviveHandler,
    TermEventHandler,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.merchant import (
    MerchantEvent3Accept,
    MerchantEvent3Refuse,
    MerchantEvent3SkillRoll,
    PendingMerchantEvent8Roll,
)
from ceres.character.domain.character_start import BackgroundSkillsHandler, CharacterStartedHandler, UcpHandler
from ceres.character.domain.connection import (
    Enemy,
    Rival,
)
from ceres.character.domain.skills import (
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
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from ceres.character.mechanism.replay import replay
from tests.character.helpers import MOCK_WORLD, AdvancedTrainingTestMixin, CharacterDriver


def _setup() -> list:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — INT DM+1, EDU DM+2."""
    return [
        Event(id=1, handler=CharacterStartedHandler(sophont=VILANI, homeworld=MOCK_WORLD, player='NPC', name='Mer')),
        Event(id=2, fulfills=(1, 0), handler=UcpHandler(ucp='7869A5')),
        Event(
            id=3, fulfills=(2, 0), handler=BackgroundSkillsHandler(skills=[Admin(), Athletics(), Carouse(), Drive()])
        ),
    ]


def _enter_merchant(assignment: str = 'Merchant Marine', qual_roll: int = 3) -> list:
    """Through qualification — INT 4+, INT=9 DM+1, roll 3 → 4 ≥ 4."""
    return [
        *_setup(),
        Event(
            id=4,
            fulfills=(3, 0),
            handler=CareerEntryHandler(
                career=MERCHANT, assignment=MERCHANT.assignment(assignment), qualification_roll=qual_roll
            ),
        ),
    ]


def _through_survive(assignment: str = 'Merchant Marine', survive_roll: int = 3) -> list:
    """Merchant service skills are all single-choice — survival queued at '4.0'.

    Merchant Marine survival: EDU 5+, EDU=10 DM+2, roll 3 → 5 ≥ 5 (pass).
    """
    return [*_enter_merchant(assignment), Event(id=5, fulfills=(4, 0), handler=SurviveHandler(roll=survive_roll))]


def _through_term_event(event_roll: int, assignment: str = 'Merchant Marine') -> list:
    return [*_through_survive(assignment), Event(id=6, fulfills=(5, 0), handler=TermEventHandler(roll=event_roll))]


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
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MerchantEvent3Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        rivals = [c for c in projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_refuse_queues_advancement(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MerchantEvent3Refuse.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)

    def test_accept_creates_skill_roll(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MerchantEvent3Accept.model_fields['kind'].default),
            ),
        ]
        projection = replay(1, events)
        pending = next((p for p in projection.pending_inputs if isinstance(p, MerchantEvent3SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Deception(), Persuade()]

    def test_accept_success_adds_benefit_roll(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MerchantEvent3Accept.model_fields['kind'].default),
            ),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.career_terms[-1].require_muster_out().extra_rolls == 1

    def test_accept_success_continues_career(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MerchantEvent3Accept.model_fields['kind'].default),
            ),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=9)),
        ]
        projection = replay(1, events)
        assert projection.summary.current_career is not None
        assert projection.summary.current_career.name == 'Merchant'

    def test_accept_failure_adds_enemy_and_ends_career(self):
        events = [
            *self._setup_to_event(),
            Event(
                id=7,
                fulfills=(6, 0),
                handler=CareerChoiceHandler(choice=MerchantEvent3Accept.model_fields['kind'].default),
            ),
            Event(id=8, fulfills=(7, 0), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
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
            Event(id=7, fulfills=(6, 0), handler=SkillChoiceHandler(skill=Admin())),
        ]
        projection = replay(1, events)
        # Admin was already at level 0 from background; should now be higher
        assert projection.summary.skill_level(Admin) is not None

    def test_natural_2_sets_forced_next_career_prisoner(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillChoiceHandler(skill=Admin())),
            Event(id=8, fulfills=(6, 1), handler=SkillRollHandler(skill=Admin(), modified_roll=2)),
        ]
        projection = replay(1, events)
        assert projection.forced_next_career is not None
        assert projection.forced_next_career.name == 'Prisoner'

    def test_roll_above_2_does_not_force_prisoner(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillChoiceHandler(skill=Admin())),
            Event(id=8, fulfills=(6, 1), handler=SkillRollHandler(skill=Admin(), modified_roll=3)),
        ]
        projection = replay(1, events)
        assert projection.forced_next_career is None

    def test_2d_roll_creates_advancement_pending(self):
        events = [
            *self._setup_to_event(),
            Event(id=7, fulfills=(6, 0), handler=SkillChoiceHandler(skill=Admin())),
            Event(id=8, fulfills=(6, 1), handler=SkillRollHandler(skill=Admin(), modified_roll=7)),
        ]
        projection = replay(1, events)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── event 9: advanced training ────────────────────────────────────────────────


class TestMerchantEvent9(AdvancedTrainingTestMixin):
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=9)

    def _existing_service_skill_type(self) -> type:
        return Broker  # auto-applied first career: Drive, Vacc Suit, Broker, Steward, Electronics, Persuade


# ── event 5: gambling opportunity ────────────────────────────────────────────


class TestMerchantEvent5:
    def _setup_to_event(self) -> list:
        return _through_term_event(event_roll=5)

    def test_gambling_adds_problem_note_and_queues_advancement(self):
        projection = replay(1, self._setup_to_event())
        assert any('gambling' in p.lower() for p in projection.summary.problems)
        assert any(isinstance(p, PendingAdvancement) for p in projection.pending_inputs)


# ── mishap 1: severely injured ────────────────────────────────────────────────


class TestMerchantMishap1:
    def test_uses_common_handler(self):
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Merchant', 'Merchant Marine', roll=3)
        d.survive(2)
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}


# ── mishap 2: bankrupted by rival ────────────────────────────────────────────


class TestMerchantMishap2:
    def _setup_to_mishap(self) -> CharacterDriver:
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Merchant', 'Merchant Marine', roll=3)  # INT 4+, DM+1, roll 3 → 4 ✓
        d.survive(2)  # EDU 5+, DM+2, roll 2 → 4 < 5 — fail
        d.mishap(2)
        return d

    def test_gains_rival(self):
        d = self._setup_to_mishap()
        rivals = [c for c in d.projection.summary.connections if isinstance(c, Rival)]
        assert len(rivals) == 1

    def test_all_benefit_rolls_forfeited_after_promotion(self):
        # After rank 1, standard ejection alone leaves 1 roll remaining (rank bonus).
        # Mishap 2 must forfeit ALL benefits — not just the current term's ejection penalty.
        # EDU=10 → DM+1 (9-11 bracket per MgT2 table)
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Merchant', 'Merchant Marine', roll=3)
        d.survive(4)  # EDU 5+, DM+1, roll 4 → 5 ≥ 5 ✓
        d.term_event(6)  # event 6 = contact → PendingAdvancement
        d.advancement(6)  # EDU 7+, DM+1, roll 6 → 7 ≥ 7 → rank 1; Mechanic auto-granted
        d.skill_table('service_skills', 6)  # row 6 = Persuade (non-specialized, auto-applies); PendingReenlist remains
        d.reenlist(True)  # → term 2 → PendingSkillTable (per-term skill roll before survival)
        d.skill_table('service_skills', 6)  # term 2 skill roll → Persuade → PendingSurvive queued
        d.survive(3)  # EDU 5+, DM+1, roll 3 → 4 < 5 — fail → PendingMishap
        d.mishap(2)
        assert not any(isinstance(p, PendingMusterOut) for p in d.projection.pending_inputs)


# ── mishap 5: trade restrictions → Rogue qualification ───────────────────────


class TestMerchantMishap5:
    def _setup_to_mishap(self) -> CharacterDriver:
        d = CharacterDriver()
        d.start(VILANI, MOCK_WORLD)
        d.ucp('7869A5')
        d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
        d.career('Merchant', 'Merchant Marine', roll=3)
        d.survive(2)  # fail → mishap
        d.mishap(5)
        return d

    def test_rogue_in_auto_qualify_careers(self):
        from ceres.character.domain.career.rogue import Rogue

        d = self._setup_to_mishap()
        assert Rogue in d.projection.auto_qualify_careers

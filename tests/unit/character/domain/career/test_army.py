"""Tests for the Army career — support, infantry, and cavalry assignments."""

from ceres.character.domain.career.army import (
    ArmyEvent12CommissionChoice,
    ArmyEvent12PromoteChoice,
    ArmyMishap4Cooperate,
    ArmyMishap4JoinRing,
    PendingArmyEvent6SkillRoll,
    PendingArmyEvent11SkillChoice,
)
from ceres.character.domain.career.career_events import (
    PendingAdvancement,
    PendingChoices,
    PendingMusterOut,
    PendingSkillChoice,
)
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.career.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.connection import Ally, Enemy, Rival
from ceres.character.domain.health.health_events import (
    PendingInjuryTable,
)
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, GunCombat, Leadership, Level, Tactics
from ceres.character.domain.sophont import VILANI
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver


def _make_setup() -> CharacterDriver:
    """STR=7 DEX=8 END=6 INT=9 EDU=10 SOC=5 — EDU DM+2."""
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD, name='Sgt')
    d.ucp('7869A5')
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    return d


def _enter_army(assignment: str = 'Support', qual_roll: int = 5) -> CharacterDriver:
    """Through qualification — END 5+, END=6 DM+0, roll 5 → 5 ≥ 5."""
    d = _make_setup()
    d.career('Army', assignment, roll=qual_roll)
    return d


def _through_survive(assignment: str = 'Support', survive_roll: int = 5) -> CharacterDriver:
    """Support survival: END 5+, DM+0, roll 5 → 5 ≥ 5 (pass)."""
    d = _enter_army(assignment)
    d.survive(survive_roll)
    return d


def _through_term_event(event_roll: int, assignment: str = 'Support') -> CharacterDriver:
    d = _through_survive(assignment)
    d.term_event(event_roll)
    return d


# ── qualification ─────────────────────────────────────────────────────────────


class TestArmyQualification:
    def test_success_enters_career(self):
        # END 5+, END=6, DM+0, roll 5 → 5 ≥ 5
        d = _enter_army()
        assert d.projection.summary.current_career is not None
        assert d.projection.summary.current_career.name == 'Army'

    def test_failure_clears_career(self):
        # END 5+, END=6, DM+0, roll 4 → 4 < 5
        d = _enter_army(qual_roll=4)
        assert d.projection.summary.current_career is None

    def test_all_three_assignments_accepted(self):
        for assignment in ('Support', 'Infantry', 'Cavalry'):
            d = _enter_army(assignment=assignment)
            assert d.projection.summary.current_assignment is not None
            assert d.projection.summary.current_assignment.name == assignment


# ── mishap 1: severely injured ────────────────────────────────────────────────


class TestArmyMishap1:
    def test_uses_common_handler(self):
        d = _enter_army()
        d.survive(4)  # END 5+, DM+0, 4 < 5 — fail
        d.mishap(1)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}


class TestArmyDirectOutcomeRows:
    def test_mishap_2_adds_enemy_and_ends_career(self):
        d = _enter_army()
        d.survive(2)
        d.mishap(2)

        assert any(isinstance(c, Enemy) for c in d.projection.summary.connections)
        assert d.projection.summary.current_career is None

    def test_mishap_5_adds_rival_and_ends_career(self):
        d = _enter_army()
        d.survive(2)
        d.mishap(5)

        assert any(isinstance(c, Rival) for c in d.projection.summary.connections)
        assert d.projection.summary.current_career is None

    def test_event_5_adds_benefit_dm(self):
        d = _through_term_event(5)

        dms = d.projection.summary.career_terms[-1].require_muster_out().benefit_roll_dms
        assert len(dms) == 1
        assert dms[0].amount == 1

    def test_event_9_adds_advancement_dm(self):
        d = _through_term_event(9)

        assert d.projection.pending_advancement_dm == 2


# ── mishap 3: skill choice and enemy ─────────────────────────────────────────


class TestArmyMishap3:
    def _setup_to_mishap(self) -> CharacterDriver:
        # Infantry survival: STR 6+, STR=7 DM+0, roll 5 → 5 < 6 — fail
        d = _enter_army('Infantry')
        d.survive(5)
        return d

    def test_mishap_3_skill_choice_is_granted(self):
        d = self._setup_to_mishap()
        d.mishap(3)
        d.choose_skill(Admin())
        assert d.projection.summary.skill_level(Admin) is not None

    def test_mishap_3_gains_enemy(self):
        d = self._setup_to_mishap()
        d.mishap(3)
        assert any(c.kind == 'connection_enemy' for c in d.projection.summary.connections)


# ── mishap 4: illegal activity ────────────────────────────────────────────────


class TestArmyMishap4:
    def _setup_to_mishap(self) -> CharacterDriver:
        d = _enter_army()
        d.survive(4)  # END 5+, DM+0, 4 < 5 — fail
        return d

    def test_mishap_4_creates_choice_pending(self):
        d = self._setup_to_mishap()
        d.mishap(4)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {ArmyMishap4JoinRing, ArmyMishap4Cooperate}

    def test_join_ring_adds_ally(self):
        d = self._setup_to_mishap()
        d.mishap(4)
        d.career_choice(ArmyMishap4JoinRing)
        allies = [c for c in d.projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 1

    def test_join_ring_ends_career(self):
        d = self._setup_to_mishap()
        d.mishap(4)
        d.career_choice(ArmyMishap4JoinRing)
        assert d.projection.summary.current_career is None

    def test_join_ring_loses_benefit_roll(self):
        # 1 term + rank 0 normally = 1 muster roll; join_ring loses it → 0 muster rolls
        d = self._setup_to_mishap()
        d.mishap(4)
        d.career_choice(ArmyMishap4JoinRing)
        assert not any(isinstance(p, PendingMusterOut) for p in d.projection.pending_inputs)

    def test_cooperate_no_ally(self):
        d = self._setup_to_mishap()
        d.mishap(4)
        d.career_choice(ArmyMishap4Cooperate)
        allies = [c for c in d.projection.summary.connections if isinstance(c, Ally)]
        assert len(allies) == 0

    def test_cooperate_keeps_benefit_roll(self):
        # 1 term + rank 0 = 1 muster roll; cooperate keeps it
        d = self._setup_to_mishap()
        d.mishap(4)
        d.career_choice(ArmyMishap4Cooperate)
        assert any(isinstance(p, PendingMusterOut) for p in d.projection.pending_inputs)

    def test_cooperate_ends_career(self):
        d = self._setup_to_mishap()
        d.mishap(4)
        d.career_choice(ArmyMishap4Cooperate)
        assert d.projection.summary.current_career is None


# ── event 6: brutal ground war ────────────────────────────────────────────────


class TestArmyEvent6:
    def _setup_to_event(self) -> CharacterDriver:
        return _through_term_event(event_roll=6)

    def test_creates_edu_skill_roll_pending(self):
        d = self._setup_to_event()
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingArmyEvent6SkillRoll)), None)
        assert pending is not None
        assert pending.options == [Chars.EDU]

    def test_success_creates_skill_choice(self):
        d = self._setup_to_event()
        d.skill_roll(Admin(), modified_roll=9)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        assert pending.options == [GunCombat(), Leadership()]

    def test_success_no_injury_problem(self):
        d = self._setup_to_event()
        d.skill_roll(Admin(), modified_roll=9)
        assert not any('injur' in p.lower() for p in d.projection.summary.problems)

    def test_failure_queues_injury_table(self):
        d = self._setup_to_event()
        d.skill_roll(Admin(), modified_roll=7)
        assert any(isinstance(p, PendingInjuryTable) for p in d.projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        d = self._setup_to_event()
        d.skill_roll(Admin(), modified_roll=7)
        assert any(isinstance(p, PendingAdvancement) for p in d.projection.pending_inputs)


# ── event 8: advanced training ────────────────────────────────────────────────


class TestArmyEvent8:
    def _setup_to_event(self) -> CharacterDriver:
        return _through_term_event(event_roll=8)

    def test_creates_edu_skill_roll_pending(self):
        d = self._setup_to_event()
        pending = next(
            (p for p in d.projection.pending_inputs if isinstance(p, PendingAdvancedTrainingSkillRoll)),
            None,
        )
        assert pending is not None
        assert pending.options == [Chars.EDU]

    def test_success_creates_skill_choice_with_existing_skills(self):
        d = self._setup_to_event()
        d.skill_roll(Admin(), modified_roll=9)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingSkillChoice)), None)
        assert pending is not None
        # Army service skills (auto-applied): Athletics, Gun Combat, Recon, Melee, Heavy Weapons
        assert any(isinstance(o, Athletics) for o in pending.options)

    def test_failure_no_skill_choice(self):
        d = self._setup_to_event()
        d.skill_roll(Admin(), modified_roll=7)
        assert not any(isinstance(p, PendingSkillChoice) for p in d.projection.pending_inputs)

    def test_failure_creates_advancement_pending(self):
        d = self._setup_to_event()
        d.skill_roll(Admin(), modified_roll=7)
        assert any(isinstance(p, PendingAdvancement) for p in d.projection.pending_inputs)


# ── event 11: commanding officer interest ─────────────────────────────────────


class TestArmyEvent11:
    def _setup_to_event(self) -> CharacterDriver:
        return _through_term_event(event_roll=11)

    def test_creates_skill_choice_pending(self):
        d = self._setup_to_event()
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingArmyEvent11SkillChoice)), None)
        assert pending is not None

    def test_skill_choice_includes_tactics_military(self):
        d = self._setup_to_event()
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingArmyEvent11SkillChoice)), None)
        assert pending is not None
        assert any(isinstance(o, Tactics) for o in pending.options)

    def test_choosing_tactics_military_grants_specialty(self):
        d = self._setup_to_event()
        d.choose_career_skill(Tactics(military=Level(value=1)))
        tac = next((s for s in d.projection.summary.skills if isinstance(s, Tactics)), None)
        assert tac is not None
        assert tac.military.value == 1

    def test_tactics_military_not_offered_if_already_at_level_1(self):
        d = _through_survive()
        d.term_event(11)
        # Grant Tactics(military) 1 first, then check options
        d.projection.summary.skills.append(Tactics(military=Level(value=1)))
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingArmyEvent11SkillChoice)), None)
        assert pending is not None
        opts = pending.input_specs(d.projection)
        # Only AdvancementDmOption should remain (Tactics(military) already at 1)
        assert len(opts[0].options) == 1
        assert 'Tactics' not in opts[0].options[0][0]


# ── event 12: heroism in battle ───────────────────────────────────────────────


class TestArmyEvent12:
    def _setup_to_event(self) -> CharacterDriver:
        return _through_term_event(event_roll=12)

    def test_first_term_offers_commission_choice(self):
        d = self._setup_to_event()
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {ArmyEvent12CommissionChoice, ArmyEvent12PromoteChoice}

    def test_commission_choice_sets_officer_rank(self):
        d = self._setup_to_event()
        d.career_choice(ArmyEvent12CommissionChoice)
        assert d.projection.summary.rank == 1
        assert d.projection.summary.career_terms[-1].commission is True

    def test_promote_choice_increments_rank(self):
        d = self._setup_to_event()
        rank_before = d.projection.summary.rank or 0
        d.career_choice(ArmyEvent12PromoteChoice)
        # Rank should have increased (auto-advance queues more pendings, just check rank changed)
        assert d.projection.summary.rank == rank_before + 1

    def test_already_commissioned_auto_promotes(self):
        # First term: commission via event 12
        d = _through_survive()
        d.term_event(12)
        d.career_choice(ArmyEvent12CommissionChoice)
        # After commission: Leadership 1 auto-granted, PendingSkillTable queued
        # + PendingAssignmentChangeChoice (age<34, allows_assignment_change)
        d.skill_table('service_skills', 3)  # GunCombat: no choice, reenlist already queued
        d.reenlist(True)  # same assignment → new term starts, queues PendingSkillTable
        # Second term: needs skill table before survival
        d.skill_table('service_skills', 4)  # Recon → PendingSurvive queued
        d.survive(5)
        d.term_event(12)
        # Already commissioned → no commission choice
        assert not any(
            isinstance(p, PendingChoices) and any(isinstance(c, ArmyEvent12CommissionChoice) for c in p.choices)
            for p in d.projection.pending_inputs
        )

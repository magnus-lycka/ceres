"""Tests for the Army career — support, infantry, and cavalry assignments."""

from ceres.character.careers.army import ArmyMishap4Cooperate, ArmyMishap4JoinRing, PendingArmyEvent6SkillRoll
from ceres.character.careers.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.characteristics import Chars
from ceres.character.events import (
    PendingAdvancement,
    PendingChoices,
    PendingMusterOut,
    PendingSkillChoice,
)
from ceres.character.skills import Admin, Athletics, Carouse, Drive, GunCombat, Leadership
from ceres.character.sophonts import VILANI
from ceres.character.state import Ally
from tests.character.helpers import MOCK_WORLD, CharacterDriver


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
            assert d.projection.summary.current_assignment == assignment


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

    def test_failure_adds_injury_problem(self):
        d = self._setup_to_event()
        d.skill_roll(Admin(), modified_roll=7)
        assert any('injur' in p.lower() for p in d.projection.summary.problems)

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

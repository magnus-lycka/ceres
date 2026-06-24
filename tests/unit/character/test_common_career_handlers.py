"""Tests for shared career handlers."""

from ceres.character.domain.career.career_events import PendingCareerChoice, PendingChoices
from ceres.character.domain.career.common import CommonMishap1DoubleRoll, CommonMishap1Severe
from ceres.character.domain.health.health_events import (
    PendingDoubleInjuryRoll,
    PendingNearlyKilled,
    PendingSeverelyInjured,
)
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive
from ceres.character.domain.sophont import VILANI
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver


def _setup_through_mishap1() -> CharacterDriver:
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('7869A5')
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    d.career('Citizen', 'Corporate', roll=4)
    d.survive(2)
    d.mishap(1)
    return d


class TestCommonMishap1Handler:
    def test_creates_choice_between_severe_and_double_roll(self):
        d = _setup_through_mishap1()
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingChoices)), None)
        assert pending is not None
        assert {type(c) for c in pending.choices} == {CommonMishap1Severe, CommonMishap1DoubleRoll}

    def test_severe_branch_queues_severely_injured_pending(self):
        # Injury table result 2 = roll 1D, reduce chosen physical stat by that amount
        d = _setup_through_mishap1()
        d.career_choice(CommonMishap1Severe)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingSeverelyInjured)), None)
        assert pending is not None

    def test_severe_branch_ends_career(self):
        d = _setup_through_mishap1()
        d.career_choice(CommonMishap1Severe)
        assert d.projection.summary.current_career is None

    def test_double_roll_branch_queues_double_injury_roll(self):
        d = _setup_through_mishap1()
        d.career_choice(CommonMishap1DoubleRoll)
        pending = next((p for p in d.projection.pending_inputs if isinstance(p, PendingDoubleInjuryRoll)), None)
        assert pending is not None

    def test_double_roll_branch_ends_career(self):
        d = _setup_through_mishap1()
        d.career_choice(CommonMishap1DoubleRoll)
        assert d.projection.summary.current_career is None

    def test_double_roll_injury_result_precedes_career_choice(self):
        # After resolving the double roll, the injury result must come before any career choice
        d = _setup_through_mishap1()
        d.career_choice(CommonMishap1DoubleRoll)
        d.double_injury_roll(1, 1)  # min=1 → nearly killed
        pendings = d.projection.pending_inputs
        nearly_killed_idx = next((i for i, p in enumerate(pendings) if isinstance(p, PendingNearlyKilled)), None)
        career_idx = next((i for i, p in enumerate(pendings) if isinstance(p, PendingCareerChoice)), None)
        assert nearly_killed_idx is not None
        if career_idx is not None:
            assert nearly_killed_idx < career_idx

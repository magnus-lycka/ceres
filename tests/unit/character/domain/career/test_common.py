"""Unit tests for career common mishap handlers."""

from ceres.character.domain.career.career_events import PendingChoices, SurviveHandler
from ceres.character.domain.career.common import (
    CommonMishap1DoubleRoll,
    CommonMishap1Handler,
    CommonMishap1Severe,
    handle_advanced_training,
)
from ceres.character.domain.career.common_pending import PendingAdvancedTrainingSkillRoll
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.health.health_events import PendingDoubleInjuryRoll, PendingSeverelyInjured
from ceres.character.domain.skills import Admin, Athletics, Carouse, Drive, GunCombat
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver

_UCP = '7869A9'


def _in_army_mid_term() -> CharacterProjection:
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp(_UCP)
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    d.career('Army', 'Support', roll=5)
    d.rank_bonus_choice(GunCombat())
    d.survive(5)
    d.term_event(5)
    d.commission(attempt=False)
    d.advancement(5)
    return d.projection


class TestHandleAdvancedTraining:
    def test_queues_pending(self):
        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='T', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        handle_advanced_training(proj, event_id=5, pending_idx=0)
        assert any(isinstance(p, PendingAdvancedTrainingSkillRoll) for p in proj.pending_inputs)

    def test_custom_threshold_stored(self):
        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='T', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        handle_advanced_training(proj, event_id=5, pending_idx=0, threshold=10)
        pending = next(p for p in proj.pending_inputs if isinstance(p, PendingAdvancedTrainingSkillRoll))
        assert pending.threshold == 10

    def test_returns_incremented_idx(self):
        proj = CharacterProjection(
            character_id=1,
            summary=CharacterSummary(name='T', sophont=VILANI, homeworld=MOCK_WORLD),
        )
        result = handle_advanced_training(proj, event_id=5, pending_idx=2)
        assert result == 3


class TestCommonMishap1Handler:
    def test_queues_pending_choices(self):
        proj = _in_army_mid_term()
        CommonMishap1Handler().handle(proj, event_id=99, pending_idx=0)
        assert any(isinstance(p, PendingChoices) for p in proj.pending_inputs)

    def test_two_choices_offered(self):
        proj = _in_army_mid_term()
        CommonMishap1Handler().handle(proj, event_id=99, pending_idx=0)
        choices = next(p for p in proj.pending_inputs if isinstance(p, PendingChoices))
        assert len(choices.choices) == 2

    def test_returns_incremented_idx(self):
        proj = _in_army_mid_term()
        result = CommonMishap1Handler().handle(proj, event_id=99, pending_idx=0)
        assert result == 1


def _any_event() -> Event:
    return Event(handler=SurviveHandler(roll=5))


class TestCommonMishap1Severe:
    def test_queues_severely_injured(self):
        proj = _in_army_mid_term()
        CommonMishap1Severe().handle(proj, _any_event())
        assert any(isinstance(p, PendingSeverelyInjured) for p in proj.pending_inputs)

    def test_ejects_by_default(self):
        proj = _in_army_mid_term()
        CommonMishap1Severe().handle(proj, _any_event())
        assert proj.summary.current_career is None

    def test_stay_in_career_preserves_career(self):
        proj = _in_army_mid_term()
        CommonMishap1Severe(stay_in_career=True).handle(proj, _any_event())
        assert proj.summary.current_career is not None


class TestCommonMishap1DoubleRoll:
    def test_queues_double_injury_roll(self):
        proj = _in_army_mid_term()
        CommonMishap1DoubleRoll().handle(proj, _any_event())
        assert any(isinstance(p, PendingDoubleInjuryRoll) for p in proj.pending_inputs)

    def test_ejects_by_default(self):
        proj = _in_army_mid_term()
        CommonMishap1DoubleRoll().handle(proj, _any_event())
        assert proj.summary.current_career is None

    def test_stay_in_career_preserves_career(self):
        proj = _in_army_mid_term()
        CommonMishap1DoubleRoll(stay_in_career=True).handle(proj, _any_event())
        assert proj.summary.current_career is not None

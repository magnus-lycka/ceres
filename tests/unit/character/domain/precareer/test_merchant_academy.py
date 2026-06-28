"""Unit tests for merchant_academy.py — MerchantAcademyPreCareer and subclasses."""

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.merchant_academy import (
    MerchantAcademyBusinessPreCareer,
    MerchantAcademyShipboardPreCareer,
)
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD

_BUSINESS = MerchantAcademyBusinessPreCareer()
_SHIPBOARD = MerchantAcademyShipboardPreCareer()


def _proj() -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(
            name='T',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.INT: 9, Chars.EDU: 7},
        ),
    )


def _event() -> Event:
    from ceres.character.domain.career.career_events import SurviveHandler

    return Event(handler=SurviveHandler(roll=5))


class TestMerchantAcademyEntryData:
    def test_entry_is_int_9_plus(self):
        assert _BUSINESS.entry.characteristic == Chars.INT
        assert _BUSINESS.entry.target == 9

    def test_soc_bonus_at_8(self):
        assert _BUSINESS.entry_soc_bonus_min == 8
        assert _BUSINESS.entry_soc_bonus == 1

    def test_graduation_is_int_7_plus(self):
        assert _BUSINESS.graduation.characteristic == Chars.INT
        assert _BUSINESS.graduation.target == 7

    def test_graduation_dms(self):
        assert _BUSINESS.graduation_dms.get('EDU_8+') == 1
        assert _BUSINESS.graduation_dms.get('SOC_8+') == 1

    def test_honours_target(self):
        assert _BUSINESS.honours_target == 11

    def test_business_curriculum_table(self):
        assert _BUSINESS.curriculum_table == 'assignment3'

    def test_shipboard_curriculum_table(self):
        assert _SHIPBOARD.curriculum_table == 'assignment1'


class TestMerchantAcademyApplyEntry:
    def test_queues_service_skill_choice_at_level_1(self):
        proj = _proj()
        _BUSINESS.make_term().apply_entry(proj, _event(), pending_idx=0)
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(choices) == 1
        assert choices[0].level == 1

    def test_grants_curriculum_skills(self):
        proj = _proj()
        _BUSINESS.make_term().apply_entry(proj, _event(), pending_idx=0)
        assert len(proj.summary.skills) > 0


class TestMerchantAcademyApplyGraduation:
    def test_queues_one_curriculum_skill_choice(self):
        proj = _proj()
        _BUSINESS.make_term().apply_graduation(proj, _event(), honours=False)
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(choices) == 1
        assert choices[0].level == 1

    def test_grants_edu_plus_1(self):
        proj = _proj()
        _BUSINESS.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.EDU] == 8

    def test_adds_rank_problem(self):
        proj = _proj()
        _BUSINESS.make_term().apply_graduation(proj, _event(), honours=False)
        assert any('rank 1' in p for p in proj.summary.problems)

    def test_honours_adds_rank_2_problem(self):
        proj = _proj()
        _BUSINESS.make_term().apply_graduation(proj, _event(), honours=True)
        assert any('rank 2' in p for p in proj.summary.problems)

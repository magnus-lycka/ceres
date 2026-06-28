"""Unit tests for school_of_hard_knocks.py — SchoolOfHardKnocksPreCareer."""

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.precareer.school_of_hard_knocks import SchoolOfHardKnocksPreCareer
from ceres.character.domain.skills import Carouse, GunCombat
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD

_SOHK = SchoolOfHardKnocksPreCareer()


def _proj(extra: dict | None = None) -> CharacterProjection:
    chars = {Chars.SOC: 5}
    chars.update(extra or {})
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(
            name='T',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics=chars,
        ),
    )


def _event() -> Event:
    from ceres.character.domain.career.career_events import SurviveHandler

    return Event(handler=SurviveHandler(roll=5))


class TestSchoolOfHardKnocksData:
    def test_no_char_check_entry(self):
        assert _SOHK.entry is None

    def test_entry_pick_count_is_2(self):
        assert _SOHK.entry_pick_count == 2

    def test_graduation_is_int_7_plus(self):
        assert _SOHK.graduation.characteristic == Chars.INT
        assert _SOHK.graduation.target == 7

    def test_graduation_dm_end_9_plus(self):
        assert _SOHK.graduation_dms.get('END_9+') == 1

    def test_honours_target(self):
        assert _SOHK.honours_target == 11

    def test_eight_skill_choices(self):
        assert len(_SOHK.skill_choices) == 8


class TestSchoolOfHardKnocksGraduation:
    def test_queues_three_level_0_choices(self):
        proj = _proj()
        _SOHK.make_term().apply_graduation(proj, _event(), honours=False)
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(choices) == 3
        assert all(c.level == 0 for c in choices)

    def test_grants_gun_combat(self):
        proj = _proj()
        _SOHK.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.skill_level(GunCombat, 0) == 0

    def test_reduces_soc_by_1(self):
        proj = _proj()
        _SOHK.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.SOC] == 4

    def test_soc_cannot_go_below_0(self):
        proj = _proj({Chars.SOC: 0})
        _SOHK.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.SOC] == 0

    def test_honours_grants_carouse_1(self):
        proj = _proj()
        _SOHK.make_term().apply_graduation(proj, _event(), honours=True)
        assert proj.summary.skill_level(Carouse, 0) == 1

    def test_honours_queues_four_choices(self):
        proj = _proj()
        _SOHK.make_term().apply_graduation(proj, _event(), honours=True)
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(choices) == 4

    def test_adds_commission_dm_problem(self):
        proj = _proj()
        _SOHK.make_term().apply_graduation(proj, _event(), honours=False)
        assert any('commission' in p.lower() for p in proj.summary.problems)

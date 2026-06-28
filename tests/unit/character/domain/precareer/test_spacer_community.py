"""Unit tests for spacer_community.py — SpacerCommunityPreCareer."""

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.precareer.spacer_community import SpacerCommunityPreCareer
from ceres.character.domain.skills import JackOfAllTrades, Pilot
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD

_SPACER = SpacerCommunityPreCareer()


def _proj(extra: dict | None = None) -> CharacterProjection:
    chars = {Chars.DEX: 7, Chars.SOC: 5}
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


class TestSpacerCommunityData:
    def test_no_char_check_entry(self):
        assert _SPACER.entry is None

    def test_entry_pick_count_is_2(self):
        assert _SPACER.entry_pick_count == 2

    def test_graduation_is_int_8_plus(self):
        assert _SPACER.graduation.characteristic == Chars.INT
        assert _SPACER.graduation.target == 8

    def test_graduation_dm_dex_6_plus(self):
        assert _SPACER.graduation_dms.get('DEX_6+') == 1

    def test_honours_target(self):
        assert _SPACER.honours_target == 12

    def test_five_skill_choices(self):
        assert len(_SPACER.skill_choices) == 5


class TestSpacerGraduation:
    def test_queues_two_level_0_and_one_level_1_choice(self):
        proj = _proj()
        _SPACER.make_term().apply_graduation(proj, _event(), honours=False)
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        levels = sorted(c.level for c in choices)
        assert levels == [0, 0, 1]

    def test_grants_pilot(self):
        proj = _proj()
        _SPACER.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.skill_level(Pilot, 0) == 0

    def test_grants_dex_plus_1(self):
        proj = _proj()
        _SPACER.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.DEX] == 8

    def test_reduces_soc_by_2(self):
        proj = _proj()
        _SPACER.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.SOC] == 3

    def test_soc_cannot_go_below_0(self):
        proj = _proj({Chars.SOC: 1})
        _SPACER.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.SOC] == 0

    def test_adds_qualification_dm_1(self):
        proj = _proj()
        _SPACER.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.pending_qualification_dm == 1

    def test_honours_grants_jack_of_all_trades_1(self):
        proj = _proj()
        _SPACER.make_term().apply_graduation(proj, _event(), honours=True)
        assert proj.summary.skill_level(JackOfAllTrades, 0) == 1

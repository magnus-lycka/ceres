"""Unit tests for colonial_upbringing.py — ColonialUprbringingPreCareer."""

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.colonial_upbringing import ColonialUprbringingPreCareer
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.skills import JackOfAllTrades, Leadership
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD

_COLONIAL = ColonialUprbringingPreCareer()


def _proj() -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(
            name='T',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.END: 7},
        ),
    )


def _event() -> Event:
    from ceres.character.domain.career.career_events import SurviveHandler

    return Event(handler=SurviveHandler(roll=5))


class TestColonialUprbringingData:
    def test_no_char_check_entry(self):
        assert _COLONIAL.entry is None

    def test_graduation_is_int_8_plus(self):
        assert _COLONIAL.graduation.characteristic == Chars.INT
        assert _COLONIAL.graduation.target == 8

    def test_graduation_dm_end_8_plus(self):
        assert _COLONIAL.graduation_dms.get('END_8+') == 1

    def test_honours_target(self):
        assert _COLONIAL.honours_target == 12

    def test_eleven_skill_choices(self):
        assert len(_COLONIAL.skill_choices) == 11


class TestColonialGraduation:
    def test_queues_three_level_1_choices(self):
        proj = _proj()
        _COLONIAL.make_term().apply_graduation(proj, _event(), honours=False)
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(choices) == 3
        assert all(c.level == 1 for c in choices)

    def test_grants_jack_of_all_trades_1(self):
        proj = _proj()
        _COLONIAL.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.skill_level(JackOfAllTrades, 0) == 1

    def test_grants_end_plus_1(self):
        proj = _proj()
        _COLONIAL.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.END] == 8

    def test_adds_edu_reduction_problem(self):
        proj = _proj()
        _COLONIAL.make_term().apply_graduation(proj, _event(), honours=False)
        assert any('EDU' in p for p in proj.summary.problems)

    def test_honours_grants_leadership_1(self):
        proj = _proj()
        _COLONIAL.make_term().apply_graduation(proj, _event(), honours=True)
        assert proj.summary.skill_level(Leadership, 0) == 1

    def test_honours_queues_four_choices(self):
        proj = _proj()
        _COLONIAL.make_term().apply_graduation(proj, _event(), honours=True)
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(choices) == 4

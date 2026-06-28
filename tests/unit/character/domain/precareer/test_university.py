"""Unit tests for university.py — UniversityPreCareer and UniversityTerm."""

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
from ceres.character.domain.precareer.university import UniversityPreCareer, UniversityTerm, _precareer_skill_options
from ceres.character.domain.skills import Admin
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD

_UNIVERSITY = UniversityPreCareer()


def _proj() -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(
            name='T',
            sophont=VILANI,
            homeworld=MOCK_WORLD,
            characteristics={Chars.EDU: 8},
        ),
    )


def _event() -> Event:
    from ceres.character.domain.career.career_events import SurviveHandler

    return Event(handler=SurviveHandler(roll=5))


class TestUniversityEntryData:
    def test_entry_is_edu_6_plus(self):
        assert _UNIVERSITY.entry.characteristic == Chars.EDU
        assert _UNIVERSITY.entry.target == 6

    def test_soc_bonus_at_soc_9(self):
        assert _UNIVERSITY.entry_soc_bonus_min == 9
        assert _UNIVERSITY.entry_soc_bonus == 1

    def test_entry_term_dm_at_2_terms(self):
        assert _UNIVERSITY.entry_term_dms[2] == -1

    def test_entry_term_dm_at_3_terms(self):
        assert _UNIVERSITY.entry_term_dms[3] == -2

    def test_graduation_is_int_6_plus(self):
        assert _UNIVERSITY.graduation.characteristic == Chars.INT
        assert _UNIVERSITY.graduation.target == 6

    def test_honours_target(self):
        assert _UNIVERSITY.honours_target == 10

    def test_twelve_skill_choices(self):
        assert len(_UNIVERSITY.skill_choices) == 12


class TestPrecareerSkillOptions:
    def test_returns_sorted_list(self):
        options = _precareer_skill_options(_UNIVERSITY)
        names = [type(s).name() for s in options]
        assert names == sorted(names)

    def test_no_duplicates(self):
        options = _precareer_skill_options(_UNIVERSITY)
        names = [type(s).name() for s in options]
        assert len(names) == len(set(names))


class TestUniversityTermApplyEntry:
    def test_grants_edu_plus_1(self):
        proj = _proj()
        _UNIVERSITY.make_term().apply_entry(proj, _event(), pending_idx=0)
        assert proj.summary.characteristics[Chars.EDU] == 9

    def test_queues_two_skill_choices(self):
        proj = _proj()
        _UNIVERSITY.make_term().apply_entry(proj, _event(), pending_idx=0)
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert len(choices) == 2

    def test_first_choice_level_0_second_level_1(self):
        proj = _proj()
        _UNIVERSITY.make_term().apply_entry(proj, _event(), pending_idx=0)
        choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
        assert choices[0].level == 0
        assert choices[1].level == 1

    def test_returns_pending_idx_plus_2(self):
        proj = _proj()
        assert _UNIVERSITY.make_term().apply_entry(proj, _event(), pending_idx=0) == 2


class TestUniversityTermApplyGraduation:
    def _term_with_skill(self) -> UniversityTerm:
        term = _UNIVERSITY.make_term()
        assert isinstance(term, UniversityTerm)
        term.pending_skills = [Admin()]
        return term

    def test_grants_pending_skills(self):
        proj = _proj()
        self._term_with_skill().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.skill_level(Admin, 0) == 1

    def test_clears_pending_skills_after_grant(self):
        term = self._term_with_skill()
        term.apply_graduation(_proj(), _event(), honours=False)
        assert term.pending_skills == []

    def test_grants_edu_plus_1(self):
        proj = _proj()
        _UNIVERSITY.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.EDU] == 9

    def test_qualification_dm_1_without_honours(self):
        proj = _proj()
        _UNIVERSITY.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.pending_qualification_dm == 1

    def test_qualification_dm_2_with_honours(self):
        proj = _proj()
        _UNIVERSITY.make_term().apply_graduation(proj, _event(), honours=True)
        assert proj.pending_qualification_dm == 2

    def test_returns_0(self):
        proj = _proj()
        assert _UNIVERSITY.make_term().apply_graduation(proj, _event(), honours=False) == 0

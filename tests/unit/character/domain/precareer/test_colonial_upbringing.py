"""Unit tests for colonial_upbringing.py — ColonialUprbringingPreCareer."""

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.colonial_upbringing import ColonialGraduationPath, ColonialUprbringingPreCareer
from ceres.character.domain.precareer.precareer_data import PrecareerSkillChoice
from ceres.character.domain.skills import (
    Admin,
    Animals,
    Athletics,
    Carouse,
    Drive,
    JackOfAllTrades,
    Leadership,
    Level,
    Medic,
    ProfessionSkill,
    Survival,
    skill_instances,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver

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


class TestColonialProfessionChoice:
    """Profession is a broad skill: pick one Profession skill at level 0, never a speciality (RIC-001)."""

    def test_asks_for_one_skill_at_level_0(self):
        (entry,) = [e for e in _COLONIAL.skill_choices if isinstance(e, PrecareerSkillChoice)]
        proj = _proj()
        entry.apply('Colonial Upbringing', proj, event_id=1, pending_idx=0)
        (pending,) = proj.pending_inputs
        assert pending.instruction == 'Colonial Upbringing: choose one skill at level 0'


class TestColonialGraduation:
    def test_grants_jack_of_all_trades_1(self):
        proj = _proj()
        _COLONIAL.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.skill_level(JackOfAllTrades, 0) == 1

    def test_grants_end_plus_1(self):
        proj = _proj()
        _COLONIAL.make_term().apply_graduation(proj, _event(), honours=False)
        assert proj.summary.characteristics[Chars.END] == 8

    def test_honours_grants_leadership_1(self):
        proj = _proj()
        _COLONIAL.make_term().apply_graduation(proj, _event(), honours=True)
        assert proj.summary.skill_level(Leadership, 0) == 1


def _colonial_after_event(event_roll: int = 12) -> CharacterDriver:
    """STR 7 DEX 8 END 9 INT 10 EDU 10 SOC 7, through the Colonial Upbringing term's event.

    Graduation is INT 8+ with DM+1 for INT 10 and DM+1 for END 8+.
    """
    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('789AA7')
    d.background_skills([Admin(), Athletics(), Carouse(), Drive()])
    d.precareer(ColonialUprbringingPreCareer, roll=7)
    d.precareer_skill(skill_instances(ProfessionSkill)[0])
    d.precareer_event(event_roll)
    return d


def _graduate(d: CharacterDriver) -> CharacterDriver:
    d.precareer_graduation(8)  # 8 + 2 = 10: graduates, without honours
    d.precareer_skill(Medic())
    d.colonial_graduation_path(ColonialGraduationPath.INCREASE)
    d.precareer_skill(Survival())
    return d


def _edu(d: CharacterDriver) -> int:
    return d.projection.summary.characteristics[Chars.EDU]


class TestColonialSecondTerm:
    """RIC-002: Colonial Upbringing is two standard terms, so the first career starts at 26.

    The second term is mandatory and offers no career choice. A graduate loses EDU D3 in it;
    a non-graduate serves it too, without the EDU loss. A draft (event 11) skips it.
    """

    def test_a_graduate_rolls_for_the_second_term_before_choosing_a_career(self):
        d = _graduate(_colonial_after_event())
        assert d.projection.summary.age == 22
        assert not d.has_career_choice()

    def test_a_graduate_starts_the_first_career_at_26(self):
        d = _graduate(_colonial_after_event())
        d.colonial_second_term(2)
        assert d.projection.summary.age == 26
        assert d.has_career_choice()

    def test_a_graduate_loses_the_d3_rolled_from_edu(self):
        d = _graduate(_colonial_after_event())
        d.colonial_second_term(3)
        assert _edu(d) == 7

    def test_the_upbringing_is_two_terms(self):
        d = _graduate(_colonial_after_event())
        d.colonial_second_term(1)
        assert d.projection.summary.terms_started_in_pre_and_careers == 2

    def test_a_non_graduate_serves_the_second_term_without_losing_edu(self):
        d = _colonial_after_event()
        d.precareer_graduation(2)  # a natural 2 never graduates
        assert d.projection.summary.age == 26
        assert _edu(d) == 10
        assert d.has_career_choice()

    def test_event_3_fails_graduation_and_still_serves_the_second_term(self):
        d = _colonial_after_event(event_roll=3)
        assert d.projection.summary.age == 26
        assert _edu(d) == 10
        assert d.has_career_choice()

    def test_a_draft_skips_the_second_term(self):
        d = _colonial_after_event(event_roll=11)
        assert d.projection.summary.age == 22
        assert d.has_career_choice()

    def test_age_and_edu_are_not_left_as_problems(self):
        d = _graduate(_colonial_after_event())
        d.colonial_second_term(2)
        assert not any('Colonial' in problem for problem in d.projection.summary.problems)


class TestColonialSecondTermHistory:
    def test_a_graduate_is_told_the_second_term_and_the_edu_lost(self):
        d = _graduate(_colonial_after_event())
        d.colonial_second_term(2)
        assert d.projection.creation_history[-1] == (
            'Term 2 (Colonial Upbringing): Another four years of colonial life. EDU decreased from 10 to 8.'
        )

    def test_a_non_graduate_is_told_the_second_term_only(self):
        d = _colonial_after_event()
        d.precareer_graduation(2)
        assert d.projection.creation_history[-1] == (
            'Term 2 (Colonial Upbringing): Another four years of colonial life.'
        )


def _level(d: CharacterDriver, skill_cls: type, speciality: str = 'level') -> int | None:
    held = next((s for s in d.projection.summary.skills if type(s) is skill_cls), None)
    return None if held is None else getattr(held, speciality).value


class TestColonialGraduationBenefits:
    """Companion p.32, as read by RIC-033:

    - Increase one listed skill still at level 0 to level 1.
    - Then either gain any two listed skills at level 1, or increase one listed skill held by one level.
    - Jack-of-all-Trades 1. Honours: Leadership 1, and may raise another listed skill still at 0 to 1.
    """

    def test_first_offers_the_listed_skills_still_at_level_0(self):
        d = _colonial_after_event()
        d.precareer_graduation(8)
        options = d.precareer_skill_options()
        assert 'Medic' in options
        assert 'Athletics (Dexterity)' in options
        assert 'Survival' not in options  # already at 1
        assert 'Carouse' not in options  # a background skill, not on the Colonial list

    def test_first_raises_the_chosen_skill_to_level_1(self):
        d = _colonial_after_event()
        d.precareer_graduation(8)
        d.precareer_skill(Medic())
        assert _level(d, Medic) == 1

    def test_two_skills_gains_two_listed_skills_at_level_1(self):
        d = _colonial_after_event()
        d.precareer_graduation(8)
        d.precareer_skill(Medic())
        d.colonial_graduation_path(ColonialGraduationPath.TWO_SKILLS)
        d.precareer_skill(Animals(handling=Level(value=1)))
        d.precareer_skill(Animals(veterinary=Level(value=1)))
        assert _level(d, Animals, 'handling') == 1
        assert _level(d, Animals, 'veterinary') == 1

    def test_two_skills_offers_nothing_already_held_at_level_1(self):
        d = _colonial_after_event()
        d.precareer_graduation(8)
        d.precareer_skill(Medic())
        d.colonial_graduation_path(ColonialGraduationPath.TWO_SKILLS)
        d.precareer_skill(Animals(handling=Level(value=1)))
        options = d.precareer_skill_options()
        assert 'Animals (Handling)' not in options
        assert 'Animals (Veterinary)' in options
        assert 'Medic' not in options
        assert 'Survival' not in options

    def test_increase_offers_the_listed_skills_held(self):
        d = _colonial_after_event()
        d.precareer_graduation(8)
        d.precareer_skill(Medic())
        d.colonial_graduation_path(ColonialGraduationPath.INCREASE)
        options = d.precareer_skill_options()
        assert 'Survival' in options
        assert 'Medic' in options
        assert 'Carouse' not in options  # held, but not on the Colonial list

    def test_increase_raises_a_listed_skill_by_one_level(self):
        d = _graduate(_colonial_after_event())  # Medic 0 -> 1, then Survival 1 -> 2
        assert _level(d, Medic) == 1
        assert _level(d, Survival) == 2

    def test_increase_is_the_only_choice_on_that_path(self):
        d = _graduate(_colonial_after_event())
        assert d.precareer_skill_choices_left() == 0

    def test_honours_grants_leadership_and_another_listed_skill_still_at_0(self):
        d = _colonial_after_event()
        d.precareer_graduation(10)  # 10 + 2 = 12: honours
        d.precareer_skill(Medic())
        d.colonial_graduation_path(ColonialGraduationPath.INCREASE)
        d.precareer_skill(Survival())
        assert _level(d, Leadership) == 1
        options = d.precareer_skill_options()
        assert 'Medic' not in options
        assert 'Recon' in options

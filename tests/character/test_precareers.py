from typing import ClassVar

from ceres.character.domain.career.career_data import (
    CharCheck,
    GainConnectionEntry,
    GainSkillEntry,
    LifeEventEntry,
    RolledConnectionsEntry,
)
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.colonial_upbringing import ColonialUprbringingPreCareer
from ceres.character.domain.precareer.loader import load_precareers, precareer_of_type
from ceres.character.domain.precareer.merchant_academy import (
    MerchantAcademyBusinessPreCareer,
    MerchantAcademyShipboardPreCareer,
)
from ceres.character.domain.precareer.military_academy import (
    ArmyAcademyPreCareer,
    MarineAcademyPreCareer,
    MilitaryAcademyPreCareer,
    NavyAcademyPreCareer,
)
from ceres.character.domain.precareer.precareer_data import PreCareerData, PrecareerSkillEntry
from ceres.character.domain.precareer.precareer_events import PreCareerEntryHandler, PreCareerGraduationHandler
from ceres.character.domain.precareer.psionic_community import PsionicCommunityPreCareer
from ceres.character.domain.precareer.school_of_hard_knocks import SchoolOfHardKnocksPreCareer
from ceres.character.domain.precareer.spacer_community import SpacerCommunityPreCareer
from ceres.character.domain.precareer.university import UniversityPreCareer
from ceres.character.domain.skills import Admin, Electronics, Pilot, ScienceSkill, skill_instances
from ceres.character.mechanism.event_base import Event


def _entry(precareer_type: type[PreCareerData]) -> CharCheck:
    entry = precareer_of_type(precareer_type).entry
    assert entry is not None
    return entry


def _graduation(precareer_type: type[PreCareerData]) -> CharCheck:
    graduation = precareer_of_type(precareer_type).graduation
    assert graduation is not None
    return graduation


def test_core_precareers_are_loaded():
    precareers = load_precareers()

    assert {
        'Army Academy',
        'Colonial Upbringing',
        'Marine Academy',
        'Merchant Academy (Business)',
        'Merchant Academy (Shipboard)',
        'Navy Academy',
        'Psionic Community',
        'School of Hard Knocks',
        'Spacer Community',
        'University',
    } == {precareer.name for precareer in precareers}


def test_all_precareers_are_four_years():
    assert {precareer.duration_years for precareer in load_precareers()} == {4}


def test_university_entry_and_graduation_rules_are_loaded():
    university = precareer_of_type(UniversityPreCareer)

    assert _entry(UniversityPreCareer).characteristic == Chars.EDU
    assert _entry(UniversityPreCareer).target == 6
    assert _graduation(UniversityPreCareer).characteristic == Chars.INT
    assert _graduation(UniversityPreCareer).target == 6
    assert university.honours_target == 10
    assert [type(s).name() for s in university.skill_choices[0].skill_options] == ['Admin']
    assert {type(s).name() for s in university.skill_choices[-1].skill_options} == {
        'Life Science',
        'Physical Science',
        'Robotic Science',
        'Social Science',
        'Space Science',
    }


def test_military_academies_have_distinct_entry_and_same_graduation():
    assert _entry(ArmyAcademyPreCareer).characteristic == Chars.END
    assert _entry(ArmyAcademyPreCareer).target == 7
    assert _entry(MarineAcademyPreCareer).characteristic == Chars.END
    assert _entry(MarineAcademyPreCareer).target == 8
    assert _entry(NavyAcademyPreCareer).characteristic == Chars.INT
    assert _entry(NavyAcademyPreCareer).target == 8

    for academy_type in (ArmyAcademyPreCareer, MarineAcademyPreCareer, NavyAcademyPreCareer):
        academy = precareer_of_type(academy_type)
        assert isinstance(academy, MilitaryAcademyPreCareer)
        assert _graduation(academy_type).characteristic == Chars.INT
        assert _graduation(academy_type).target == 7
        assert academy.honours_target == 11
        assert academy.tied_career is not None
        assert academy.service_skills_from.name == academy.tied_career


def test_precareer_events_are_loaded_once_for_all_precareers():
    university = precareer_of_type(UniversityPreCareer)

    assert set(university.events) == set(range(2, 13))
    assert isinstance(university.events[5], GainSkillEntry)
    assert isinstance(university.events[6], RolledConnectionsEntry)
    assert isinstance(university.events[7], LifeEventEntry)
    assert isinstance(university.events[10], GainConnectionEntry)


def test_companion_precareers_are_loaded():
    colonial = precareer_of_type(ColonialUprbringingPreCareer)
    merchant_business = precareer_of_type(MerchantAcademyBusinessPreCareer)
    merchant_shipboard = precareer_of_type(MerchantAcademyShipboardPreCareer)
    psionic = precareer_of_type(PsionicCommunityPreCareer)
    hard_knocks = precareer_of_type(SchoolOfHardKnocksPreCareer)
    spacer = precareer_of_type(SpacerCommunityPreCareer)

    assert colonial.entry_requirement == 'Automatic if homeworld is TL8-'
    assert _graduation(ColonialUprbringingPreCareer).target == 8
    assert [type(s).name() for s in colonial.skill_choices[-1].skill_options] == ['Survival']

    assert _entry(MerchantAcademyBusinessPreCareer).characteristic == Chars.INT
    assert _entry(MerchantAcademyBusinessPreCareer).target == 9
    assert merchant_business.curriculum_table == 'assignment3'
    assert _entry(MerchantAcademyShipboardPreCareer).characteristic == Chars.INT
    assert _entry(MerchantAcademyShipboardPreCareer).target == 9
    assert merchant_shipboard.curriculum_table == 'assignment1'

    assert psionic.entry_requirement == 'PSI 8+, DM+1 if INT 8+'
    assert psionic.graduation_requirement == 'PSI 6+, DM+1 if INT 8+'

    assert hard_knocks.entry_requirement == 'Automatic if SOC 6-'
    assert _graduation(SchoolOfHardKnocksPreCareer).target == 7

    assert spacer.entry_requirement == 'Automatic if homeworld size code 0; INT 4+, DM+1 if DEX 8+'
    assert _graduation(SpacerCommunityPreCareer).target == 8


# ── PrecareerSkillEntry properties ───────────────────────────────────────────


def test_precareer_skill_entry_properties_with_none_skill():
    entry = PrecareerSkillEntry(skill=None, level=1)
    assert entry.skill_options == []
    assert entry.category_label == 'skill'
    assert entry.grant_skill() is None


def test_precareer_skill_entry_properties_with_list_skill():
    sciences = skill_instances(ScienceSkill)
    entry = PrecareerSkillEntry(skill=sciences, level=1)
    assert entry.skill_options == sciences
    assert entry.category_label == 'skill'
    assert entry.grant_skill() is None


def test_precareer_skill_entry_category_label_for_single_skill():
    entry = PrecareerSkillEntry(skill=Admin(), level=1)
    assert entry.category_label == 'Admin'


def test_precareer_skill_entry_grant_skill_specialised():
    # Pilot has multiple spec fields — _skill_at_level takes the multi-field path
    entry = PrecareerSkillEntry(skill=Pilot(), level=1)
    granted = entry.grant_skill()
    assert granted is not None


# ── PreCareerData.apply_entry with entry_pick_count == 0 and list skill ──────


def test_precareer_apply_entry_pick_count_0_list_skill_queues_choice():
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
    from ceres.character.domain.sophont import VILANI
    from tests.character.helpers import MOCK_WORLD

    sciences = skill_instances(ScienceSkill)

    class TestPrecareer(PreCareerData):
        name: ClassVar[str] = 'TestPrecareer'
        source: ClassVar[str] = 'test'
        entry_pick_count: ClassVar[int] = 0
        skill_choices: ClassVar[list[PrecareerSkillEntry]] = [
            PrecareerSkillEntry(skill=Admin(), level=1),  # fixed grant
            PrecareerSkillEntry(skill=sciences, level=1),  # list → queued choice
        ]

    precareer = TestPrecareer()
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    event = Event(handler=PreCareerEntryHandler(precareer=precareer, roll=9))
    pending_idx = precareer.apply_entry(proj, event, 0)

    assert proj.summary.skill_level(Admin) == 1
    assert pending_idx == 1
    skill_choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
    assert len(skill_choices) == 1
    assert skill_choices[0].level == 1


# ── PreCareerData.apply_entry with entry_pick_count > 0 ──────────────────────


def test_precareer_apply_entry_pick_count_nonzero_with_list_and_pool():
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.domain.precareer.precareer_events import PendingPreCareerSkillChoice
    from ceres.character.domain.sophont import VILANI
    from tests.character.helpers import MOCK_WORLD

    sciences = skill_instances(ScienceSkill)

    class TestPrecareer2(PreCareerData):
        name: ClassVar[str] = 'TestPrecareer2'
        source: ClassVar[str] = 'test'
        entry_pick_count: ClassVar[int] = 2
        skill_choices: ClassVar[list[PrecareerSkillEntry]] = [
            PrecareerSkillEntry(skill=Admin(), level=1),  # fixed grant (level >= 1)
            PrecareerSkillEntry(skill=sciences, level=1),  # list at level 1 → queued choice
            PrecareerSkillEntry(skill=Electronics(), level=0),  # level 0 → choice pool
            PrecareerSkillEntry(skill=Pilot(), level=0),  # level 0 → choice pool
        ]

    precareer = TestPrecareer2()
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    event = Event(handler=PreCareerEntryHandler(precareer=precareer, roll=9))
    precareer.apply_entry(proj, event, 0)

    assert proj.summary.skill_level(Admin) == 1
    skill_choices = [p for p in proj.pending_inputs if isinstance(p, PendingPreCareerSkillChoice)]
    # 1 for the science list + 2 from the pick pool
    assert len(skill_choices) == 3
    pool_choices = [p for p in skill_choices if p.level == 0]
    assert len(pool_choices) == 2
    assert all(Electronics() in p.options or Pilot() in p.options for p in pool_choices)


# ── PreCareerData.apply_entry skips None-skill entries ───────────────────────


def test_precareer_apply_entry_skips_none_skill_entries():
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.domain.sophont import VILANI
    from tests.character.helpers import MOCK_WORLD

    class TestNoneSkill(PreCareerData):
        name: ClassVar[str] = 'TestNoneSkill'
        source: ClassVar[str] = 'test'
        entry_pick_count: ClassVar[int] = 0
        skill_choices: ClassVar[list[PrecareerSkillEntry]] = [
            PrecareerSkillEntry(skill=None, level=1),
            PrecareerSkillEntry(skill=Admin(), level=1),
        ]

    precareer = TestNoneSkill()
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    precareer.apply_entry(proj, Event(handler=PreCareerEntryHandler(precareer=precareer, roll=9)), 0)
    assert proj.summary.skill_level(Admin) == 1


def test_precareer_apply_entry_pick_count_nonzero_skips_none_skill():
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.domain.sophont import VILANI
    from tests.character.helpers import MOCK_WORLD

    class TestNoneSkill2(PreCareerData):
        name: ClassVar[str] = 'TestNoneSkill2'
        source: ClassVar[str] = 'test'
        entry_pick_count: ClassVar[int] = 1
        skill_choices: ClassVar[list[PrecareerSkillEntry]] = [
            PrecareerSkillEntry(skill=None, level=1),
            PrecareerSkillEntry(skill=Pilot(), level=0),
        ]

    precareer = TestNoneSkill2()
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    precareer.apply_entry(proj, Event(handler=PreCareerEntryHandler(precareer=precareer, roll=9)), 0)
    assert len(proj.pending_inputs) == 1


# ── PreCareerData.apply_graduation default ────────────────────────────────────


def test_precareer_apply_graduation_base_returns_zero():
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.domain.sophont import VILANI
    from tests.character.helpers import MOCK_WORLD

    class TestGrad(PreCareerData):
        name: ClassVar[str] = 'TestGrad'
        source: ClassVar[str] = 'test'

    precareer = TestGrad()
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    result = precareer.apply_graduation(proj, Event(handler=PreCareerGraduationHandler(roll=9)), honours=False)
    assert result == 0


# ── PreCareerData.apply_failed_graduation default ────────────────────────────


def test_precareer_apply_failed_graduation_base_is_noop():
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.domain.sophont import VILANI
    from tests.character.helpers import MOCK_WORLD

    class TestPrecareer3(PreCareerData):
        name: ClassVar[str] = 'TestPrecareer3'
        source: ClassVar[str] = 'test'

    precareer = TestPrecareer3()
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    event = Event(handler=PreCareerGraduationHandler(roll=3))
    before_pendings = len(proj.pending_inputs)
    precareer.apply_failed_graduation(proj, event)
    assert len(proj.pending_inputs) == before_pendings

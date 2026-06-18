from ceres.character.domain.career.career_data import CharCheck, GainSkillEffect, LifeEventEffect
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.loader import load_precareers
from ceres.character.domain.precareer.precareer_data import PreCareerData, PrecareerSkillEntry
from ceres.character.domain.precareer.precareer_events import PreCareerEntryHandler, PreCareerGraduationHandler
from ceres.character.domain.skills import Admin, Electronics, Pilot, ScienceSkill, skill_instances
from ceres.character.mechanism.event_base import Event


def _entry(name: str) -> CharCheck:
    entry = load_precareers()[name].entry
    assert entry is not None
    return entry


def _graduation(name: str) -> CharCheck:
    graduation = load_precareers()[name].graduation
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
    } == set(precareers)


def test_all_precareers_are_four_years():
    assert {precareer.duration_years for precareer in load_precareers().values()} == {4}


def test_university_entry_and_graduation_rules_are_loaded():
    university = load_precareers()['University']

    assert _entry('University').characteristic == Chars.EDU
    assert _entry('University').target == 6
    assert _graduation('University').characteristic == Chars.INT
    assert _graduation('University').target == 6
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
    precareers = load_precareers()

    assert _entry('Army Academy').characteristic == Chars.END
    assert _entry('Army Academy').target == 7
    assert _entry('Marine Academy').characteristic == Chars.END
    assert _entry('Marine Academy').target == 8
    assert _entry('Navy Academy').characteristic == Chars.INT
    assert _entry('Navy Academy').target == 8

    for name in ('Army Academy', 'Marine Academy', 'Navy Academy'):
        academy = precareers[name]
        assert _graduation(name).characteristic == Chars.INT
        assert _graduation(name).target == 7
        assert academy.honours_target == 11
        assert academy.tied_career is not None
        assert academy.service_skills_from is not None
        assert academy.service_skills_from.name == academy.tied_career


def test_precareer_events_are_loaded_once_for_all_precareers():
    university = load_precareers()['University']

    assert set(university.events) == set(range(2, 13))
    assert isinstance(university.events[5].effects[0], GainSkillEffect)
    assert isinstance(university.events[7].effects[0], LifeEventEffect)


def test_companion_precareers_are_loaded():
    precareers = load_precareers()

    assert precareers['Colonial Upbringing'].entry_requirement == 'Automatic if homeworld is TL8-'
    assert _graduation('Colonial Upbringing').target == 8
    assert [type(s).name() for s in precareers['Colonial Upbringing'].skill_choices[-1].skill_options] == ['Survival']

    assert _entry('Merchant Academy (Business)').characteristic == Chars.INT
    assert _entry('Merchant Academy (Business)').target == 9
    assert precareers['Merchant Academy (Business)'].curriculum_table == 'assignment3'
    assert _entry('Merchant Academy (Shipboard)').characteristic == Chars.INT
    assert _entry('Merchant Academy (Shipboard)').target == 9
    assert precareers['Merchant Academy (Shipboard)'].curriculum_table == 'assignment1'

    assert precareers['Psionic Community'].entry_requirement == 'PSI 8+, DM+1 if INT 8+'
    assert precareers['Psionic Community'].graduation_requirement == 'PSI 6+, DM+1 if INT 8+'

    assert precareers['School of Hard Knocks'].entry_requirement == 'Automatic if SOC 6-'
    assert _graduation('School of Hard Knocks').target == 7

    assert (
        precareers['Spacer Community'].entry_requirement == 'Automatic if homeworld size code 0; INT 4+, DM+1 if DEX 8+'
    )
    assert _graduation('Spacer Community').target == 8


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
    precareer = PreCareerData(
        name='TestPrecareer',
        source='test',
        events={},
        entry_pick_count=0,
        skill_choices=[
            PrecareerSkillEntry(skill=Admin(), level=1),  # fixed grant
            PrecareerSkillEntry(skill=sciences, level=1),  # list → queued choice
        ],
    )
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    event = Event(id=5, handler=PreCareerEntryHandler(precareer='TestPrecareer', roll=9))
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
    precareer = PreCareerData(
        name='TestPrecareer2',
        source='test',
        events={},
        entry_pick_count=2,
        skill_choices=[
            PrecareerSkillEntry(skill=Admin(), level=1),  # fixed grant (level >= 1)
            PrecareerSkillEntry(skill=sciences, level=1),  # list at level 1 → queued choice
            PrecareerSkillEntry(skill=Electronics(), level=0),  # level 0 → choice pool
            PrecareerSkillEntry(skill=Pilot(), level=0),  # level 0 → choice pool
        ],
    )
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    event = Event(id=5, handler=PreCareerEntryHandler(precareer='TestPrecareer2', roll=9))
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

    precareer = PreCareerData(
        name='TestNoneSkill',
        source='test',
        events={},
        entry_pick_count=0,
        skill_choices=[
            PrecareerSkillEntry(skill=None, level=1),
            PrecareerSkillEntry(skill=Admin(), level=1),
        ],
    )
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    precareer.apply_entry(proj, Event(id=5, handler=PreCareerEntryHandler(precareer='TestNoneSkill', roll=9)), 0)
    assert proj.summary.skill_level(Admin) == 1


def test_precareer_apply_entry_pick_count_nonzero_skips_none_skill():
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.domain.sophont import VILANI
    from tests.character.helpers import MOCK_WORLD

    precareer = PreCareerData(
        name='TestNoneSkill2',
        source='test',
        events={},
        entry_pick_count=1,
        skill_choices=[
            PrecareerSkillEntry(skill=None, level=1),
            PrecareerSkillEntry(skill=Pilot(), level=0),
        ],
    )
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    precareer.apply_entry(proj, Event(id=5, handler=PreCareerEntryHandler(precareer='TestNoneSkill2', roll=9)), 0)
    assert len(proj.pending_inputs) == 1


# ── PreCareerData.apply_graduation default ────────────────────────────────────


def test_precareer_apply_graduation_base_returns_zero():
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.domain.sophont import VILANI
    from tests.character.helpers import MOCK_WORLD

    precareer = PreCareerData(name='TestGrad', source='test', events={})
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    result = precareer.apply_graduation(proj, Event(id=7, handler=PreCareerGraduationHandler(roll=9)), honours=False)
    assert result == 0


# ── PreCareerData.apply_failed_graduation default ────────────────────────────


def test_precareer_apply_failed_graduation_base_is_noop():
    from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
    from ceres.character.domain.sophont import VILANI
    from tests.character.helpers import MOCK_WORLD

    precareer = PreCareerData(name='TestPrecareer3', source='test', events={})
    proj = CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD),
    )
    event = Event(id=6, handler=PreCareerGraduationHandler(roll=3))
    before_pendings = len(proj.pending_inputs)
    precareer.apply_failed_graduation(proj, event)
    assert len(proj.pending_inputs) == before_pendings

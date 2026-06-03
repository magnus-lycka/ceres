from typing import Any

from ceres.character import skills as character_skills
from ceres.character.characteristics import Chars
from ceres.character.events import PreCareerEntryEvent, PreCareerGraduationEvent
from ceres.character.precareers.loader import load_precareers
from ceres.character.precareers.military_academy import MilitaryAcademyPreCareer
from ceres.character.sophonts import VILANI
from ceres.character.state import CharacterProjection, CharacterSummary, EffectTrigger
from tests.character.helpers import MOCK_WORLD


def _projection(**summary_kwargs: Any) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Cadet', sophont=VILANI, homeworld=MOCK_WORLD, **summary_kwargs),
    )


def _skill_types(projection: CharacterProjection) -> set[type[character_skills.Skill]]:
    return {type(skill) for skill in projection.summary.skills}


def test_entry_grants_direct_tied_career_service_skills_and_skips_choice_lists(monkeypatch):
    class FakeCareer:
        def skill_table(self, name: str):
            assert name == 'service_skills'
            return type(
                'SkillTable',
                (),
                {
                    'entries': [
                        [character_skills.Drive(), character_skills.VaccSuit()],
                        character_skills.Athletics(),
                        character_skills.GunCombat(),
                        character_skills.Recon(),
                        character_skills.Melee(),
                        character_skills.HeavyWeapons(),
                    ]
                },
            )()

    monkeypatch.setattr('ceres.character.careers.loader.load_careers', lambda: {'Army': FakeCareer()})
    projection = _projection()
    academy = load_precareers()['Army Academy']

    next_pending_idx = academy.apply_entry(
        projection,
        PreCareerEntryEvent(id=7, precareer='Army Academy', roll=9),
        pending_idx=3,
    )

    assert next_pending_idx == 3
    assert _skill_types(projection) == {
        character_skills.Athletics,
        character_skills.GunCombat,
        character_skills.HeavyWeapons,
        character_skills.Melee,
        character_skills.Recon,
    }
    assert character_skills.Drive not in _skill_types(projection)
    assert character_skills.VaccSuit not in _skill_types(projection)


def test_entry_is_noop_when_tied_career_is_unknown(monkeypatch):
    monkeypatch.setattr('ceres.character.careers.loader.load_careers', lambda: {})
    projection = _projection()
    academy = MilitaryAcademyPreCareer(
        name='Ghost Academy',
        source='Test',
        service_skills_from='No Such Career',
        events={},
    )

    next_pending_idx = academy.apply_entry(
        projection,
        PreCareerEntryEvent(id=8, precareer='Ghost Academy', roll=9),
        pending_idx=2,
    )

    assert next_pending_idx == 2
    assert projection.summary.skills == []


def test_graduation_increases_edu_queues_auto_qualification_and_notes_manual_benefits():
    projection = _projection(characteristics={Chars.EDU: 7, Chars.SOC: 6})
    academy = load_precareers()['Navy Academy']

    next_pending_idx = academy.apply_graduation(
        projection,
        PreCareerGraduationEvent(id=9, roll=10),
        honours=False,
    )

    assert next_pending_idx == 0
    assert projection.summary.characteristics[Chars.EDU] == 8
    assert projection.summary.characteristics[Chars.SOC] == 6
    assert projection.scheduled_effects[0].trigger == EffectTrigger.AUTO_QUALIFY
    assert projection.scheduled_effects[0].source_event_id == 9
    assert projection.scheduled_effects[0].consume is True
    assert projection.scheduled_effects[0].effect == {'career': 'Navy'}
    assert projection.summary.problems == [
        'Navy Academy graduation: if entering Navy, select any three Service Skills and increase them to level 1. '
        'Apply manually.',
        'Navy Academy graduation: entitled to a commission roll at the start of your first Navy career term with DM+2. '
        'Apply manually.',
    ]


def test_graduation_with_honours_also_increases_soc_and_marks_automatic_commission_note():
    projection = _projection(characteristics={Chars.EDU: 7, Chars.SOC: 6})
    academy = load_precareers()['Marine Academy']

    academy.apply_graduation(
        projection,
        PreCareerGraduationEvent(id=10, roll=12),
        honours=True,
    )

    assert projection.summary.characteristics[Chars.EDU] == 8
    assert projection.summary.characteristics[Chars.SOC] == 7
    assert projection.scheduled_effects[0].effect == {'career': 'Marines'}
    assert projection.summary.problems[-1].endswith('with DM+2 (automatic with honours). Apply manually.')


def test_failed_graduation_above_natural_two_allows_auto_entry_without_commission():
    projection = _projection()
    academy = load_precareers()['Army Academy']

    academy.apply_failed_graduation(
        projection,
        PreCareerGraduationEvent(id=11, roll=3),
    )

    assert projection.scheduled_effects[0].trigger == EffectTrigger.AUTO_QUALIFY
    assert projection.scheduled_effects[0].source_event_id == 11
    assert projection.scheduled_effects[0].consume is True
    assert projection.scheduled_effects[0].effect == {'career': 'Army', 'no_commission': True}
    assert projection.summary.problems == [
        'Army Academy: failed graduation (roll > 2) — may still enter Army automatically, '
        'but no commission roll in first term.'
    ]


def test_failed_graduation_on_natural_two_has_no_auto_entry_effect():
    projection = _projection()
    academy = load_precareers()['Army Academy']

    academy.apply_failed_graduation(
        projection,
        PreCareerGraduationEvent(id=12, roll=2),
    )

    assert projection.scheduled_effects == []
    assert projection.summary.problems == []


def test_auto_qualify_effect_bypasses_qualification_roll():
    from ceres.character.events import CareerEvent
    from ceres.character.state import ScheduledEffect

    projection = _projection(characteristics={Chars.END: 5})
    projection.scheduled_effects.append(
        ScheduledEffect(
            trigger=EffectTrigger.AUTO_QUALIFY,
            source_event_id=5,
            effect={'career': 'Army'},
        )
    )
    CareerEvent(id=6, career='Army', assignment='Infantry', qualification_roll=0).apply(projection)

    assert projection.summary.current_career is not None
    assert projection.summary.current_career.name == 'Army'
    assert projection.scheduled_effects == []

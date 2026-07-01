from ceres.character.domain.career import ARMY
from ceres.character.domain.career.army import Army
from ceres.character.domain.career.career_events import (
    CareerEntryHandler,
    PendingInitialTrainingChoice,
    PendingSkillTable,
)
from ceres.character.domain.career.marines import Marines
from ceres.character.domain.career.navy import Navy
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.precareer.loader import precareer_of_type
from ceres.character.domain.precareer.military_academy import (
    ArmyAcademyPreCareer,
    MarineAcademyPreCareer,
    NavyAcademyPreCareer,
)
from ceres.character.domain.precareer.precareer_events import PreCareerGraduationHandler
from ceres.character.domain.skills import Admin
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.event_base import Event
from tests.unit.character.helpers import MOCK_WORLD, CharacterDriver


def _projection(**summary_kwargs) -> CharacterProjection:
    return CharacterProjection(
        character_id=1,
        summary=CharacterSummary(name='Cadet', sophont=VILANI, homeworld=MOCK_WORLD, **summary_kwargs),
    )


def test_graduation_increases_edu_queues_auto_qualification_and_notes_manual_benefits():
    projection = _projection(characteristics={Chars.EDU: 7, Chars.SOC: 6})
    academy = precareer_of_type(NavyAcademyPreCareer)

    next_pending_idx = academy.apply_graduation(
        projection,
        Event(handler=PreCareerGraduationHandler(roll=10)),
        honours=False,
    )

    assert next_pending_idx == 0
    assert projection.summary.characteristics[Chars.EDU] == 8
    assert projection.summary.characteristics[Chars.SOC] == 6
    assert projection.auto_qualify_careers == [Navy]
    assert projection.summary.problems == [
        'Navy Academy graduation: if entering Navy, select any three Service Skills and increase them to level 1. '
        'Apply manually.',
        'Navy Academy graduation: entitled to a commission roll at the start of your first Navy career term with DM+2. '
        'Apply manually.',
    ]


def test_graduation_with_honours_also_increases_soc_and_marks_automatic_commission_note():
    projection = _projection(characteristics={Chars.EDU: 7, Chars.SOC: 6})
    academy = precareer_of_type(MarineAcademyPreCareer)

    academy.apply_graduation(
        projection,
        Event(handler=PreCareerGraduationHandler(roll=12)),
        honours=True,
    )

    assert projection.summary.characteristics[Chars.EDU] == 8
    assert projection.summary.characteristics[Chars.SOC] == 7
    assert projection.auto_qualify_careers == [Marines]
    assert projection.summary.problems[-1].endswith('with DM+2 (automatic with honours). Apply manually.')


def test_failed_graduation_above_natural_two_allows_auto_entry_without_commission():
    projection = _projection()
    academy = precareer_of_type(ArmyAcademyPreCareer)

    academy.apply_failed_graduation(
        projection,
        Event(handler=PreCareerGraduationHandler(roll=3)),
    )

    assert projection.auto_qualify_careers == [Army]
    assert projection.summary.problems == [
        'Army Academy: failed graduation (roll > 2) — may still enter Army automatically, '
        'but no commission roll in first term.'
    ]


def test_failed_graduation_on_natural_two_has_no_auto_entry_effect():
    projection = _projection()
    academy = precareer_of_type(ArmyAcademyPreCareer)

    academy.apply_failed_graduation(
        projection,
        Event(handler=PreCareerGraduationHandler(roll=2)),
    )

    assert projection.auto_qualify_careers == []
    assert projection.summary.problems == []


def test_auto_qualify_effect_bypasses_qualification_roll():

    projection = _projection(characteristics={Chars.END: 5})
    projection.auto_qualify_careers.append(Army)
    Event(
        id=6, handler=CareerEntryHandler(career=ARMY, assignment=ARMY.assignment('Infantry'), qualification_roll=0)
    ).apply(projection)

    assert projection.summary.current_career is not None
    assert projection.summary.current_career.name == 'Army'
    assert projection.auto_qualify_careers == []


# ── RIC-009: no repeated basic training after Military Academy ────────────────


def _army_academy_graduate() -> CharacterDriver:
    """UCP 778827: INT=8 → graduation 7+ reachable; EDU=2 → 1 background skill."""
    from ceres.character.domain.career.career_events import PendingInitialTrainingChoice
    from ceres.character.domain.skills import Drive

    d = CharacterDriver()
    d.start(VILANI, MOCK_WORLD)
    d.ucp('778827')
    d.background_skills([Admin()])
    d.precareer(ArmyAcademyPreCareer, roll=8)
    while d._find_opt(PendingInitialTrainingChoice):
        d.initial_training(Drive())
    d.precareer_event(5)
    d.precareer_graduation(8)
    return d


def test_army_academy_graduate_entering_army_gets_no_initial_training_choice():
    """RIC-009: Army Academy already administers basic training; Army career must not repeat it."""
    d = _army_academy_graduate()
    d.career(Army, 'Support', roll=7)
    assert not any(isinstance(p, PendingInitialTrainingChoice) for p in d.projection.pending_inputs)


def test_army_academy_graduate_entering_army_gets_skill_table_instead():
    """RIC-009: Army career should queue a normal skill table roll, not basic training."""
    d = _army_academy_graduate()
    d.career(Army, 'Support', roll=7)
    assert any(isinstance(p, PendingSkillTable) for p in d.projection.pending_inputs)

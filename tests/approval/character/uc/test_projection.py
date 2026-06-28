"""Approval snapshots for CharacterProjection.skill_choices, check_skill_choice, and state mutations."""

import pytest

from ceres.character.domain.career import SCOUT
from ceres.character.domain.career.career_data import CareerTerm
from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.psionics import Psionics
from ceres.character.domain.skills import (
    Admin,
    Animals,
    Electronics,
    Level,
    LifeScience,
    PhysicalScience,
    RoboticScience,
    SocialScience,
    SpaceScience,
)
from ceres.character.domain.sophont import VILANI
from ceres.character.mechanism.errors import ReplayError
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot
from tests.unit.character.helpers import MOCK_WORLD

_ext = AnnotatedJSONSnapshotExtension


def _proj(skills=None) -> CharacterProjection:
    summary = CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD, skills=skills or [])
    return CharacterProjection(character_id=1, summary=summary)


def _proj_with_term() -> CharacterProjection:
    proj = _proj()
    proj.summary.terms.append(CareerTerm(career=SCOUT, assignment=SCOUT.assignment('Courier')))
    return proj


def _choices_snap(proj: CharacterProjection, skill_types, level) -> AnnotatedSnapshot:
    choices = proj.skill_choices(skill_types, level)
    return AnnotatedSnapshot({'choices': [s.model_dump(mode='json') for s in choices]})


# ── skill_choices: non-specialised ───────────────────────────────────────────


@pytest.mark.approval
def test_skill_choices_increment_from_missing(snapshot):
    """Missing skill increments to level 1."""
    assert _choices_snap(_proj(), [Admin], None) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_skill_choices_increment_from_level_0(snapshot):
    """Level-0 skill increments to level 1."""
    assert _choices_snap(_proj([Admin(level=Level(value=0))]), [Admin], None) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_skill_choices_increment_from_level_1(snapshot):
    """Level-1 skill increments to level 2."""
    assert _choices_snap(_proj([Admin(level=Level(value=1))]), [Admin], None) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_skill_choices_capped_at_level_4(snapshot):
    """Level-4 skill has no further increment choices."""
    assert _choices_snap(_proj([Admin(level=Level(value=4))]), [Admin], None) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_skill_choices_fixed_level_1_when_missing(snapshot):
    """Fixed level 1 grant for a missing skill produces one choice."""
    assert _choices_snap(_proj(), [Admin], 1) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_skill_choices_fixed_level_1_when_already_at_1(snapshot):
    """Fixed level 1 grant produces no choices when skill is already at level 1."""
    assert _choices_snap(_proj([Admin(level=Level(value=1))]), [Admin], 1) == snapshot(extension_class=_ext)


# ── skill_choices: specialised ───────────────────────────────────────────────


@pytest.mark.approval
def test_skill_choices_specialised_from_missing(snapshot):
    """Missing specialised skill produces choices for all specialties."""
    assert _choices_snap(_proj(), [Animals], None) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_skill_choices_specialised_spec_at_level_4_excluded(snapshot):
    """A maxed specialty is excluded; others remain available."""
    assert _choices_snap(_proj([Animals(handling=Level(value=4))]), [Animals], None) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_skill_choices_multiple_science_types(snapshot):
    """All science specialties across five classes are returned."""
    assert _choices_snap(
        _proj(), [LifeScience, PhysicalScience, RoboticScience, SocialScience, SpaceScience], None
    ) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_skill_choices_multiple_types_excludes_maxed(snapshot):
    """Maxed type is excluded; other types remain."""
    assert _choices_snap(_proj([Admin(level=Level(value=4))]), [Admin, Animals], None) == snapshot(extension_class=_ext)


# ── check_skill_choice ────────────────────────────────────────────────────────


@pytest.mark.approval
def test_check_skill_choice_valid_increment(snapshot):
    proj = _proj()
    result = proj.check_skill_choice([Admin], None, Admin(level=Level(value=1)))
    assert AnnotatedSnapshot({'result': result}) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_check_skill_choice_skip_levels_invalid(snapshot):
    proj = _proj()
    result = proj.check_skill_choice([Admin], None, Admin(level=Level(value=3)))
    assert AnnotatedSnapshot({'result': result}) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_check_skill_choice_fixed_level_0(snapshot):
    proj = _proj()
    result = proj.check_skill_choice([Admin], 0, Admin())
    assert AnnotatedSnapshot({'result': result}) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_check_skill_choice_wrong_skill_type(snapshot):
    proj = _proj()
    result = proj.check_skill_choice(
        [LifeScience, PhysicalScience, RoboticScience, SocialScience, SpaceScience],
        None,
        Electronics(computers=Level(value=1)),
    )
    assert AnnotatedSnapshot({'result': result}) == snapshot(extension_class=_ext)


# ── decrease_characteristic ───────────────────────────────────────────────────


@pytest.mark.approval
def test_decrease_characteristic_floors_at_zero(snapshot):
    proj = _proj()
    proj.summary.characteristics[Chars.END] = 1
    proj.decrease_characteristic(Chars.END, amount=5)
    assert AnnotatedSnapshot(proj.summary.model_dump(mode='json')) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_decrease_psi_to_zero_removes_psionics(snapshot):
    proj = _proj()
    proj.summary.characteristics[Chars.PSI] = 1
    proj.summary.psionics = Psionics()
    proj.decrease_characteristic(Chars.PSI)
    assert AnnotatedSnapshot(proj.summary.model_dump(mode='json')) == snapshot(extension_class=_ext)


# ── projection-level state ────────────────────────────────────────────────────


@pytest.mark.approval
def test_add_advancement_dm_accumulates(snapshot):
    proj = _proj()
    proj.add_advancement_dm(2)
    proj.add_advancement_dm(1)
    assert AnnotatedSnapshot({'pending_advancement_dm': proj.pending_advancement_dm}) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_add_qualification_dm_accumulates(snapshot):
    proj = _proj()
    proj.add_qualification_dm(3)
    proj.add_qualification_dm(2)
    assert AnnotatedSnapshot({'pending_qualification_dm': proj.pending_qualification_dm}) == snapshot(
        extension_class=_ext
    )


@pytest.mark.approval
def test_add_benefit_dm_to_current_term(snapshot):
    proj = _proj_with_term()
    proj.add_benefit_dm(1)
    muster_out = proj.summary.career_terms[-1].require_muster_out()
    assert AnnotatedSnapshot(
        {'benefit_roll_dms': [dm.model_dump(mode='json') for dm in muster_out.benefit_roll_dms]}
    ) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_adjust_parole_threshold_clamped(snapshot):
    proj = _proj()
    proj.summary.parole_threshold = 2
    proj.adjust_parole_threshold(-10)
    after_floor = proj.summary.parole_threshold
    proj.adjust_parole_threshold(20)
    after_ceil = proj.summary.parole_threshold
    assert AnnotatedSnapshot({'after_floor': after_floor, 'after_ceil': after_ceil}) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_auto_qualify_deduplicates(snapshot):
    proj = _proj()
    proj.auto_qualify(type(SCOUT))
    proj.auto_qualify(type(SCOUT))
    assert AnnotatedSnapshot({'auto_qualify_careers': [c.__name__ for c in proj.auto_qualify_careers]}) == snapshot(
        extension_class=_ext
    )


@pytest.mark.approval
def test_forfeit_current_career_benefits(snapshot):
    proj = _proj_with_term()
    muster_out = proj.summary.career_terms[-1].require_muster_out()
    proj.forfeit_current_career_benefits()
    assert AnnotatedSnapshot({'lost_rolls': muster_out.lost_rolls}) == snapshot(extension_class=_ext)


@pytest.mark.approval
def test_forfeit_without_active_career_raises(snapshot):
    proj = _proj()
    try:
        proj.forfeit_current_career_benefits()
        raised = False
    except ReplayError:
        raised = True
    assert AnnotatedSnapshot({'raised': raised}) == snapshot(extension_class=_ext)

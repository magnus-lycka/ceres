import pytest

from ceres.character.domain.character_state import CharacterProjection, CharacterSummary
from ceres.character.domain.skills import (
    EXISTING_SKILLS,
    Admin,
    AnySkill,
    ArtSkill,
    BackgroundSkill,
    CreativeArt,
    Drive,
    Electronics,
    Flyer,
    GunCombat,
    LifeScience,
    Melee,
    PerformingArt,
    PhysicalScience,
    PresentationArt,
    ProfessionSkill,
    RoboticScience,
    ScienceSkill,
    SkillSpecialization,
    SocialScience,
    SpaceScience,
    WorkerProfession,
    _skill_classes,
    gain_skills,
    skill_spec,
)
from ceres.character.domain.sophont import VILANI
from tests.character.helpers import MOCK_WORLD


def _empty() -> CharacterSummary:
    return CharacterSummary(name='Test', sophont=VILANI, homeworld=MOCK_WORLD)


def _summary(*skills: AnySkill) -> CharacterSummary:
    s = _empty()
    s.skills.extend(skills)
    return s


def _apply(summary: CharacterSummary, skill: AnySkill) -> None:
    CharacterProjection(character_id=0, summary=summary).grant_skill(skill)


def _has(skills: list, cls: type, **field_values: int) -> bool:
    """True if any skill in list is an instance of cls with the given Level field values."""
    return any(isinstance(s, cls) and all(getattr(s, f).value == v for f, v in field_values.items()) for s in skills)


def test_level_can_be_set_and_incremented():
    level = Admin().level

    level.set(2)
    level += 1

    assert level.value == 3
    assert int(level) == 3


def test_simple_skill_has_one_level():
    skill = Admin()

    skill.level += 2

    assert isinstance(skill, Admin)
    assert skill.level.value == 2
    assert skill.model_dump(exclude_none=True)['level'] == {'value': 2}


def test_specialised_skill_has_one_level_per_speciality():
    skill = Electronics()

    skill.remote_ops += 1
    skill.sensors.set(2)

    assert isinstance(skill, Electronics)
    assert skill.comms.value == 0
    assert skill.remote_ops.value == 1
    assert skill.sensors.value == 2


def test_all_skills_can_be_listed_from_the_any_skill_union():
    assert Admin in _skill_classes(AnySkill)
    assert Electronics.specialities() == ('Comms', 'Computers', 'Remote Ops', 'Sensors')
    assert SpaceScience.specialities() == ('Astronomy', 'Cosmology', 'Planetology')


def test_melee_includes_companion_specialities():
    assert 'Grapple' in Melee.specialities()
    assert 'Striking' in Melee.specialities()
    assert 'Fencing' in Melee.specialities()


def test_melee_companion_specialities_are_independent_levels():
    skill = Melee()

    skill.grapple.set(2)
    skill.striking += 1

    assert skill.grapple.value == 2
    assert skill.striking.value == 1
    assert skill.fencing.value == 0
    assert skill.unarmed.value == 0


def test_skill_group_unions_can_be_listed_separately():
    assert _skill_classes(ArtSkill) == (PerformingArt, CreativeArt, PresentationArt)
    assert WorkerProfession in _skill_classes(ProfessionSkill)
    assert _skill_classes(ScienceSkill) == (
        LifeScience,
        PhysicalScience,
        RoboticScience,
        SocialScience,
        SpaceScience,
    )


# ---------------------------------------------------------------------------
# gain_skills tests — groups A through J
# ---------------------------------------------------------------------------


# A: Non-specialised skill, level=0


def test_gain_A1_nonspec_absent_level0():
    summary = _empty()
    result = gain_skills(summary, Admin, 0)
    assert len(result) == 1
    assert isinstance(result[0], Admin) and result[0].level.value == 0
    _apply(summary, result[0])
    assert summary.skill_level(Admin) == 0


def test_gain_A2_nonspec_present_at_0_level0():
    assert gain_skills(_summary(Admin()), Admin, 0) == []


def test_gain_A3_nonspec_present_above_0_level0():
    s = Admin()
    s.level.set(1)
    assert gain_skills(_summary(s), Admin, 0) == []


# B: Non-specialised skill, level=N


def test_gain_B1_nonspec_absent_level_N():
    summary = _empty()
    result = gain_skills(summary, Admin, 2)
    assert len(result) == 1
    assert isinstance(result[0], Admin) and result[0].level.value == 2
    _apply(summary, result[0])
    assert summary.skill_level(Admin) == 2


def test_gain_B2_nonspec_present_below_N():
    s = Admin()
    s.level.set(1)
    summary = _summary(s)
    result = gain_skills(summary, Admin, 2)
    assert len(result) == 1
    assert isinstance(result[0], Admin) and result[0].level.value == 2
    _apply(summary, result[0])
    assert summary.skill_level(Admin) == 2


def test_gain_B3_nonspec_present_at_N():
    s = Admin()
    s.level.set(2)
    assert gain_skills(_summary(s), Admin, 2) == []


def test_gain_B4_nonspec_present_above_N():
    s = Admin()
    s.level.set(3)
    assert gain_skills(_summary(s), Admin, 2) == []


# C: Non-specialised skill, level=None (increment)


def test_gain_C1_nonspec_absent_increment():
    summary = _empty()
    result = gain_skills(summary, Admin, None)
    assert len(result) == 1
    assert isinstance(result[0], Admin) and result[0].level.value == 1
    _apply(summary, result[0])
    assert summary.skill_level(Admin) == 1


def test_gain_C2_nonspec_present_increment():
    s = Admin()
    s.level.set(1)
    summary = _summary(s)
    result = gain_skills(summary, Admin, None)
    assert len(result) == 1
    assert isinstance(result[0], Admin) and result[0].level.value == 2
    _apply(summary, result[0])
    assert summary.skill_level(Admin) == 2


def test_gain_C3_nonspec_at_cap_increment():
    s = Admin()
    s.level.set(4)
    assert gain_skills(_summary(s), Admin, None) == []


# D: Specialised skill by class, level=0


def test_gain_D1_spec_absent_level0():
    summary = _empty()
    result = gain_skills(summary, GunCombat, 0)
    assert len(result) == 1
    assert isinstance(result[0], GunCombat)
    _apply(summary, result[0])
    assert summary.skill_level(GunCombat) == 0


def test_gain_D2_spec_present_nonzero_level0():
    gc = GunCombat()
    gc.slug.set(1)
    assert gain_skills(_summary(gc), GunCombat, 0) == []


def test_gain_D3_spec_present_all_zero_level0():
    assert gain_skills(_summary(GunCombat()), GunCombat, 0) == []


# E: Specialised skill by class, level=N (N > 0)


def test_gain_E1_spec_absent_level1():
    result = gain_skills(_empty(), GunCombat, 1)
    assert len(result) == 3
    assert _has(result, GunCombat, archaic=1)
    assert _has(result, GunCombat, energy=1)
    assert _has(result, GunCombat, slug=1)


def test_gain_E2_spec_slug_present_level1():
    gc = GunCombat()
    gc.slug.set(1)
    result = gain_skills(_summary(gc), GunCombat, 1)
    assert len(result) == 2
    assert _has(result, GunCombat, archaic=1)
    assert _has(result, GunCombat, energy=1)


def test_gain_E3_spec_all_at_N_level_N():
    gc = GunCombat()
    gc.slug.set(1)
    gc.energy.set(1)
    gc.archaic.set(1)
    assert gain_skills(_summary(gc), GunCombat, 1) == []


# F: Specialised skill by class, level=None (increment)


def test_gain_F1_spec_absent_increment():
    result = gain_skills(_empty(), GunCombat, None)
    assert len(result) == 3
    assert _has(result, GunCombat, archaic=1)
    assert _has(result, GunCombat, energy=1)
    assert _has(result, GunCombat, slug=1)


def test_gain_F2_spec_slug1_increment():
    gc = GunCombat()
    gc.slug.set(1)
    result = gain_skills(_summary(gc), GunCombat, None)
    assert _has(result, GunCombat, slug=2)
    assert _has(result, GunCombat, energy=1)
    assert _has(result, GunCombat, archaic=1)


def test_gain_F3_spec_all_at_cap_increment():
    gc = GunCombat()
    gc.slug.set(4)
    gc.energy.set(4)
    gc.archaic.set(4)
    assert gain_skills(_summary(gc), GunCombat, None) == []


def test_gain_F4_spec_one_at_cap_increment():
    gc = GunCombat()
    gc.slug.set(4)
    result = gain_skills(_summary(gc), GunCombat, None)
    assert len(result) == 2
    assert _has(result, GunCombat, energy=1)
    assert _has(result, GunCombat, archaic=1)


# G: SkillSpecialization input


def test_gain_G1_skill_spec_absent_increment():
    slug = skill_spec(GunCombat, 'Slug')
    summary = _empty()
    result = gain_skills(summary, slug, None)
    assert len(result) == 1
    assert _has(result, GunCombat, slug=1)
    _apply(summary, result[0])
    assert summary.skill_level(GunCombat) == 1


def test_gain_G2_skill_spec_present_increment():
    slug = skill_spec(GunCombat, 'Slug')
    gc = GunCombat()
    gc.slug.set(1)
    result = gain_skills(_summary(gc), slug, None)
    assert len(result) == 1
    assert _has(result, GunCombat, slug=2)


def test_gain_G3_skill_spec_at_cap_increment():
    slug = skill_spec(GunCombat, 'Slug')
    gc = GunCombat()
    gc.slug.set(4)
    assert gain_skills(_summary(gc), slug, None) == []


def test_gain_G4_skill_spec_other_spec_present_increment():
    slug = skill_spec(GunCombat, 'Slug')
    gc = GunCombat()
    gc.energy.set(2)
    result = gain_skills(_summary(gc), slug, None)
    assert len(result) == 1
    assert _has(result, GunCombat, slug=1)


def test_gain_G5_skill_spec_absent_level0():
    slug = skill_spec(GunCombat, 'Slug')
    result = gain_skills(_empty(), slug, 0)
    assert len(result) == 1
    assert isinstance(result[0], GunCombat)


def test_gain_G6_skill_spec_present_level0():
    slug = skill_spec(GunCombat, 'Slug')
    assert gain_skills(_summary(GunCombat()), slug, 0) == []


# H: Type alias spec (ScienceSkill, BackgroundSkill)


def test_gain_H1_science_none_on_sheet_level0():
    result = gain_skills(_empty(), ScienceSkill, 0)
    assert len(result) == 5
    types = {type(s) for s in result}
    assert LifeScience in types
    assert PhysicalScience in types
    assert RoboticScience in types
    assert SocialScience in types
    assert SpaceScience in types


def test_gain_H2_science_one_present_level0():
    result = gain_skills(_summary(LifeScience()), ScienceSkill, 0)
    assert len(result) == 4
    assert LifeScience not in {type(s) for s in result}


def test_gain_H3_science_all_absent_level1():
    # LifeScience=4, PhysicalScience=3, RoboticScience=2, SocialScience=7, SpaceScience=3 = 19
    result = gain_skills(_empty(), ScienceSkill, 1)
    assert len(result) == 19
    assert _has(result, LifeScience, biology=1)
    assert _has(result, SpaceScience, planetology=1)


def test_gain_H4_background_level0_empty():
    result = gain_skills(_empty(), BackgroundSkill, 0)
    types = {type(s) for s in result}
    assert Admin in types
    assert GunCombat not in types
    assert LifeScience in types


def test_gain_H5_background_admin_present_excluded():
    result = gain_skills(_summary(Admin()), BackgroundSkill, 0)
    assert Admin not in {type(s) for s in result}


# I: EXISTING_SKILLS sentinel


def test_gain_I1_existing_empty_summary():
    assert gain_skills(_empty(), EXISTING_SKILLS, None) == []


def test_gain_I2_existing_full_example():
    admin = Admin()
    admin.level.set(1)
    drive = Drive()
    drive.wheel.set(1)
    ls = LifeScience()
    ls.biology.set(2)
    summary = _summary(admin, drive, Flyer(), ls)
    result = gain_skills(summary, EXISTING_SKILLS, None)

    assert _has(result, Admin, level=2)
    assert _has(result, Drive, wheel=2)
    assert _has(result, Drive, hovercraft=1)
    assert _has(result, Flyer, airship=1)
    assert _has(result, LifeScience, biology=3)
    assert _has(result, LifeScience, genetics=1)


def test_gain_I3_existing_skill_at_cap_excluded():
    s = Admin()
    s.level.set(4)
    assert gain_skills(_summary(s), EXISTING_SKILLS, None) == []


def test_gain_I4_existing_with_level_raises():
    with pytest.raises(ValueError):
        gain_skills(_summary(Admin()), EXISTING_SKILLS, 1)


# J: SkillSpecialization validation


def test_gain_J1_skill_spec_valid():
    sp = skill_spec(GunCombat, 'Slug')
    assert sp.skill_cls is GunCombat
    assert sp.spec == 'Slug'


def test_gain_J2_skill_spec_invalid_raises():
    with pytest.raises(ValueError):
        skill_spec(GunCombat, 'Laser')


def test_gain_J3_direct_construction_also_validates():
    with pytest.raises(ValueError):
        SkillSpecialization(GunCombat, 'Laser')

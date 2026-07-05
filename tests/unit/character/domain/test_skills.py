import pytest

from ceres.character.domain.skills import (
    Admin,
    AnySkill,
    ArtSkill,
    CreativeArt,
    Electronics,
    LifeScience,
    Melee,
    PerformingArt,
    PhysicalScience,
    PresentationArt,
    ProfessionSkill,
    RoboticScience,
    ScienceSkill,
    SocialScience,
    SpaceScience,
    SpecRef,
    WorkerProfession,
    _skill_classes,
)


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


def test_class_level_specialization_access_returns_typed_ref():
    ref = Electronics.computers

    assert isinstance(ref, SpecRef)
    assert ref.skill_cls is Electronics
    assert ref.field == 'computers'


def test_spec_refs_from_different_skills_are_distinguishable():
    assert Melee.blade.skill_cls is Melee  # ty: ignore[unresolved-attribute]
    assert Electronics.sensors.skill_cls is Electronics  # ty: ignore[unresolved-attribute]


def test_class_level_access_to_unknown_specialization_raises():
    with pytest.raises(AttributeError):
        _ = Electronics.submarine


def test_class_level_spec_access_does_not_break_instance_field_access():
    skill = Electronics()
    skill.computers.set(2)

    assert skill.computers.value == 2
    assert Electronics.model_validate_json(skill.model_dump_json()).computers.value == 2


class TestSkillLabel:
    def test_non_specialised_label_is_class_name(self):
        assert Admin().label() == 'Admin'

    def test_specialised_bare_instance_label_is_class_name(self):
        assert Electronics().label() == 'Electronics'

    def test_specialised_active_field_appears_in_label(self):
        skill = Electronics()
        skill.computers.set(1)
        assert skill.label() == 'Electronics (Computers)'


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

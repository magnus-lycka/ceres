from ceres.character.skills import (
    Admin,
    AnySkill,
    ArtSkill,
    Electronics,
    Melee,
    ProfessionSkill,
    ScienceSkill,
    parse_skill_spec_option,
    skill_list,
    skill_spec_option_names,
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

    assert skill.type == 'Admin'
    assert skill.level.value == 2
    assert skill.model_dump(exclude_none=True) == {'type': 'Admin', 'level': {'value': 2}}


def test_specialised_skill_has_one_level_per_speciality():
    skill = Electronics()

    skill.remote_ops += 1
    skill.sensors.set(2)

    assert skill.type == 'Electronics'
    assert skill.comms.value == 0
    assert skill.remote_ops.value == 1
    assert skill.sensors.value == 2


def test_all_skills_can_be_listed_from_the_any_skill_union():
    skills = skill_list(AnySkill)

    assert 'Admin' in [skill.type for skill in skills]
    assert next(skill for skill in skills if skill.type == 'Electronics').specialities == (
        'Comms',
        'Computers',
        'Remote Ops',
        'Sensors',
    )
    assert next(skill for skill in skills if skill.type == 'Space Science').specialities == (
        'Astronomy',
        'Cosmology',
        'Planetology',
    )


def test_melee_includes_companion_specialities():
    melee = next(skill for skill in skill_list(AnySkill) if skill.type == 'Melee')

    assert 'Grapple' in melee.specialities
    assert 'Striking' in melee.specialities
    assert 'Fencing' in melee.specialities


def test_melee_companion_specialities_are_independent_levels():
    skill = Melee()

    skill.grapple.set(2)
    skill.striking += 1

    assert skill.grapple.value == 2
    assert skill.striking.value == 1
    assert skill.fencing.value == 0
    assert skill.unarmed.value == 0


def test_skill_group_unions_can_be_listed_separately():
    assert [skill.type for skill in skill_list(ArtSkill)] == ['Performing Art', 'Creative Art', 'Presentation Art']
    assert 'Worker Profession' in [skill.type for skill in skill_list(ProfessionSkill)]
    assert [skill.type for skill in skill_list(ScienceSkill)] == [
        'Life Science',
        'Physical Science',
        'Robotic Science',
        'Social Science',
        'Space Science',
    ]


def test_skill_spec_option_names_expands_specialised_skill():
    opts = skill_spec_option_names('Physical Science')

    assert opts == [
        'Physical Science (Chemistry)',
        'Physical Science (Physics)',
        'Physical Science (Jumpspace Physics)',
    ]


def test_skill_spec_option_names_returns_name_for_unspecialised_skill():
    opts = skill_spec_option_names('Admin')

    assert opts == ['Admin']


def test_parse_skill_spec_option_parses_spec():
    skill, spec = parse_skill_spec_option('Physical Science (Chemistry)')

    assert skill == 'Physical Science'
    assert spec == 'Chemistry'


def test_parse_skill_spec_option_returns_none_spec_for_plain_name():
    skill, spec = parse_skill_spec_option('Admin')

    assert skill == 'Admin'
    assert spec is None

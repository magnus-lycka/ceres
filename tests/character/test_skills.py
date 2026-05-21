from ceres.character.skills import Admin, AnySkill, ArtSkill, Electronics, ProfessionSkill, ScienceSkill, skill_list


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

    assert 'Admin' in [skill.name for skill in skills]
    assert next(skill for skill in skills if skill.name == 'Electronics').specialities == (
        'Comms',
        'Computers',
        'Remote Ops',
        'Sensors',
    )
    assert next(skill for skill in skills if skill.name == 'Space Science').specialities == (
        'Astronomy',
        'Cosmology',
        'Planetology',
    )


def test_skill_group_unions_can_be_listed_separately():
    assert [skill.name for skill in skill_list(ArtSkill)] == ['Performing Art', 'Creative Art', 'Presentation Art']
    assert 'Worker Profession' in [skill.name for skill in skill_list(ProfessionSkill)]
    assert [skill.name for skill in skill_list(ScienceSkill)] == [
        'Life Science',
        'Physical Science',
        'Robotic Science',
        'Social Science',
        'Space Science',
    ]

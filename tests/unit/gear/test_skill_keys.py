from typing import Annotated

from ceres.character.domain.skills import Admin, Advocate, Athletics, Skill
from ceres.gear.skill_keys import key_matches_skill, skill_classes_from_key


def test_skill_class_directly_returns_itself():
    assert skill_classes_from_key(Admin) == (Admin,)


def test_union_of_skills_returns_both():
    key = Admin | Advocate
    result = skill_classes_from_key(key)
    assert Admin in result
    assert Advocate in result


def test_annotated_skill_is_unwrapped():
    key = Annotated[Admin, 'some metadata']
    assert skill_classes_from_key(key) == (Admin,)


def test_non_skill_types_in_union_are_excluded():
    key = Admin | int
    result = skill_classes_from_key(key)
    assert result == (Admin,)


def test_key_matches_skill_true_for_direct_class():
    assert key_matches_skill(Admin, Admin) is True


def test_key_matches_skill_false_for_other_class():
    assert key_matches_skill(Admin, Advocate) is False


def test_key_matches_skill_true_for_union_member():
    key = Admin | Advocate
    assert key_matches_skill(key, Admin) is True
    assert key_matches_skill(key, Advocate) is True


def test_key_matches_skill_false_for_non_union_member():
    key = Admin | Advocate
    assert key_matches_skill(key, Athletics) is False


def test_abstract_base_skill_not_included():
    result = skill_classes_from_key(Admin)
    assert result == (Admin,)
    assert Skill not in result

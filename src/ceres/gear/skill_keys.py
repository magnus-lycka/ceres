from typing import Annotated, get_args, get_origin

from ceres.character.domain.skills import Skill

type SkillCostKey = object


def skill_classes_from_key(key: SkillCostKey) -> tuple[type[Skill], ...]:
    if hasattr(key, '__value__'):
        key = key.__value__
    if get_origin(key) is Annotated:
        key = get_args(key)[0]
    if isinstance(key, type) and issubclass(key, Skill):
        return (key,)
    return tuple(arg for arg in get_args(key) if isinstance(arg, type) and issubclass(arg, Skill))


def key_matches_skill(key: SkillCostKey, skill_cls: type[Skill]) -> bool:
    return skill_cls in skill_classes_from_key(key)

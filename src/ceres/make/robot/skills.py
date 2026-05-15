"""Skill grants and installed skill packages for robot brains."""

from dataclasses import dataclass

from ceres.shared import CeresModel


@dataclass(frozen=True)
class SkillGrant:
    """A skill at a given level granted by a brain package or option."""

    name: str
    level: int

    def __str__(self) -> str:
        return f'{self.name} {self.level}'


class SkillPackage(CeresModel):
    """An installed skill package on an Advanced (or higher) robot brain."""

    model_config = {'frozen': True}

    name: str
    level: int
    bandwidth: int


_PRIMITIVE_SKILLS: dict[str, tuple[SkillGrant, ...]] = {
    'alert': (SkillGrant('Recon', 0),),
    'clean': (SkillGrant('Profession (domestic cleaner)', 2),),
    'evade': (SkillGrant('Athletics (dexterity)', 1), SkillGrant('Stealth', 2)),
    'homing': (SkillGrant('Weapon', 1),),
    'none': (),
}


def primitive_package_skills(function: str) -> tuple[SkillGrant, ...]:
    return _PRIMITIVE_SKILLS.get(function, ())


__all__ = ['SkillGrant', 'SkillPackage', 'primitive_package_skills']

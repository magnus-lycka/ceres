"""Skill grants and installed skill packages for robot brains."""

from dataclasses import dataclass

from ceres.shared import CeresModel

# Skills whose characteristic DM is DEX (not INT).
# From refs/robot/35_skill_packages.md Standard Skill Packages table.
_DEX_SKILLS: frozenset[str] = frozenset(
    {
        'Animals',
        'Drive',
        'Flyer',
        'Gun Combat',
        'Gunner',
        'Heavy Weapons',
        'Melee',
        'Pilot',
        'Seafarer',
        'Stealth',
    }
)

# Skill grant names (full, with speciality) that use DEX DM (overrides base-name table).
# Athletics (Dexterity) specialization uses DEX even though 'Athletics' is not in _DEX_SKILLS.
_DEX_SKILL_GRANTS: frozenset[str] = frozenset({'Athletics (Dexterity)'})

# Skill grant names (full, with speciality) that use STR DM instead of INT DM.
_STR_SKILL_GRANTS: frozenset[str] = frozenset({'Athletics (Strength)'})

# Base costs (level 0) per refs/robot/35_skill_packages.md Standard Skill Packages table.
# Cost at level N = base × 10^N.
_SKILL_BASE_COSTS: dict[str, float] = {
    'Admin': 100.0,
    'Advocate': 500.0,
    'Animals': 200.0,
    'Art': 500.0,
    'Astrogation': 500.0,
    'Athletics': 100.0,
    'Broker': 200.0,
    'Carouse': 500.0,
    'Deception': 1000.0,
    'Diplomat': 500.0,
    'Drive': 100.0,
    'Electronics': 100.0,
    'Engineer': 200.0,
    'Explosives': 100.0,
    'Flyer': 100.0,
    'Gambler': 500.0,
    'Gun Combat': 100.0,
    'Gunner': 100.0,
    'Heavy Weapons': 100.0,
    'Investigate': 500.0,
    'Language': 200.0,
    'Leadership': 1000.0,
    'Mechanic': 100.0,
    'Medic': 200.0,
    'Melee': 100.0,
    'Navigation': 100.0,
    'Persuade': 500.0,
    'Pilot': 100.0,
    'Profession': 200.0,
    'Recon': 500.0,
    'Science': 200.0,
    'Seafarer': 100.0,
    'Stealth': 500.0,
    'Steward': 100.0,
    'Streetwise': 1000.0,
    'Survival': 200.0,
    'Tactics': 100.0,
}


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

    def grant_name(self) -> str:
        """Skill name for a grant; replaces speciality with (All) at level 0 (unspecialized)."""
        if self.level > 0:
            return self.name
        i = self.name.find('(')
        if i == -1:
            return self.name
        return self.name[:i] + '(All)'

    @property
    def cost(self) -> float:
        base_name = self.name.split('(')[0].strip()
        base = _SKILL_BASE_COSTS.get(base_name, 100.0)
        return base * (10.0**self.level)


_PRIMITIVE_SKILLS: dict[str, tuple[SkillGrant, ...]] = {
    'alert': (SkillGrant('Recon', 0),),
    'clean': (SkillGrant('Profession (domestic cleaner)', 2),),
    'evade': (SkillGrant('Athletics (dexterity)', 1), SkillGrant('Stealth', 2)),
    'homing': (SkillGrant('Weapon', 1),),
    'labourer': (SkillGrant('Profession (labourer)', 2),),
    'locomotion': (SkillGrant('Athletics (dexterity)', 1),),
    'none': (),
    'recon': (SkillGrant('Recon', 2), SkillGrant('Athletics (dexterity)', 1)),
    'servant': (SkillGrant('Profession (domestic servant)', 2),),
}


def primitive_package_skills(function: str) -> tuple[SkillGrant, ...]:
    return _PRIMITIVE_SKILLS.get(function, ())


class BrainSoftware(CeresModel):
    """Non-skill software installed in an Advanced (or higher) brain, consuming bandwidth.

    Used for software packages such as Universal Translator that run on the brain
    and consume bandwidth but do not grant skills.
    """

    model_config = {'frozen': True}

    name: str
    bandwidth: int
    tl: int = 0
    cost: float = 0.0


__all__ = [
    'SkillGrant',
    'SkillPackage',
    'BrainSoftware',
    'primitive_package_skills',
    '_DEX_SKILLS',
    '_DEX_SKILL_GRANTS',
    '_STR_SKILL_GRANTS',
]

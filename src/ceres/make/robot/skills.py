"""Skill grants and installed skill packages for robot brains."""

from dataclasses import dataclass
from typing import Annotated, ClassVar, Literal, cast

from pydantic import ConfigDict, Field

from ceres.character.domain import skills as character_skills
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import (
    AnySkill,
    Level,
    Skill,
    active_speciality_field,
    active_speciality_label,
    level_fields,
    speciality_label,
)
from ceres.gear.skill_keys import SkillCostKey, key_matches_skill
from ceres.shared import CeresModel


def _level(name: str | None = None):
    return Field(default_factory=Level, json_schema_extra={'name': name} if name else None)


class RobotProfession(Skill):
    type: Literal['Robot Profession'] = 'Robot Profession'
    belter: Level = _level('Belter')
    cleaning: Level = _level('cleaning')
    domestic_cleaner: Level = _level('domestic cleaner')
    domestic_servant: Level = _level('domestic servant')
    fabricator: Level = _level('Fabricator')
    gardening: Level = _level('gardening')
    labourer: Level = _level('labourer')
    robotics: Level = _level('Robotics')

    @classmethod
    def name(cls) -> str:
        return 'Profession'


class Weapon(Skill):
    type: Literal['Robot Weapon'] = 'Robot Weapon'
    level: Level = _level()

    @classmethod
    def name(cls) -> str:
        return 'Weapon'


type RobotSpecificSkill = Annotated[RobotProfession | Weapon, Field(discriminator='type')]
type RobotSkill = AnySkill | RobotSpecificSkill
type _SkillCostKey = SkillCostKey


# Skills whose characteristic DM is DEX (not INT).
# From refs/robot/35_skill_packages.md Standard Skill Packages table.
_DEX_SKILLS: frozenset[type[Skill]] = frozenset(
    {
        character_skills.Animals,
        character_skills.Drive,
        character_skills.Flyer,
        character_skills.GunCombat,
        character_skills.HeavyWeapons,
        character_skills.Melee,
        character_skills.Seafarer,
        character_skills.Stealth,
    }
)

_STR_SKILL_KEYS: frozenset[tuple[type[Skill], str | None]] = frozenset({(character_skills.Athletics, 'strength')})

_DEX_SKILL_KEYS: frozenset[tuple[type[Skill], str | None]] = frozenset(
    {
        (character_skills.Athletics, 'dexterity'),
        (character_skills.Gunner, 'screen'),
        (character_skills.Gunner, 'turret'),
        (character_skills.Pilot, 'small_craft'),
        (character_skills.Pilot, 'spacecraft'),
    }
)

_INT_SKILL_KEYS: frozenset[tuple[type[Skill], str | None]] = frozenset(
    {
        (character_skills.Animals, 'training'),
        (character_skills.Animals, 'veterinary'),
        (character_skills.Gunner, 'capital'),
        (character_skills.Gunner, 'ortillery'),
        (character_skills.Pilot, 'capital_ships'),
        (character_skills.Seafarer, 'ocean_ships'),
        (character_skills.Seafarer, 'submarine'),
    }
)

# Speciality fields with no applicable robot characteristic (e.g. Athletics/Endurance).
_NULL_SKILL_KEYS: frozenset[tuple[type[Skill], str]] = frozenset({(character_skills.Athletics, 'endurance')})

# Per refs/robot/35_skill_packages.md Standard Skill Packages table.
# Tuple: (min_tl, base_bandwidth, base_cost_cr). Cost at level N = base_cost × 10^N.
_SKILL_PACKAGE_PROPS: dict[_SkillCostKey, tuple[int, int, float]] = {
    character_skills.Admin: (8, 0, 100.0),
    character_skills.Advocate: (10, 0, 500.0),
    character_skills.Animals: (9, 0, 200.0),
    character_skills.ArtSkill: (10, 0, 500.0),
    character_skills.Astrogation: (12, 1, 500.0),
    character_skills.Athletics: (8, 0, 100.0),
    character_skills.Broker: (10, 0, 200.0),
    character_skills.Carouse: (11, 1, 500.0),
    character_skills.Deception: (13, 1, 1000.0),
    character_skills.Diplomat: (10, 1, 500.0),
    character_skills.Drive: (8, 0, 100.0),
    character_skills.Electronics: (8, 0, 100.0),
    character_skills.Engineer: (9, 0, 200.0),
    character_skills.Explosives: (8, 0, 100.0),
    character_skills.Flyer: (8, 0, 100.0),
    character_skills.Gambler: (10, 0, 500.0),
    character_skills.GunCombat: (8, 0, 100.0),
    character_skills.Gunner: (8, 0, 100.0),
    character_skills.HeavyWeapons: (8, 0, 100.0),
    character_skills.Investigate: (11, 1, 500.0),
    character_skills.Languages: (9, 0, 200.0),
    character_skills.Leadership: (13, 1, 1000.0),
    character_skills.Mechanic: (8, 0, 100.0),
    character_skills.Medic: (9, 0, 200.0),
    character_skills.Melee: (8, 0, 100.0),
    character_skills.Navigation: (8, 0, 100.0),
    character_skills.Persuade: (11, 1, 500.0),
    character_skills.Pilot: (8, 0, 100.0),
    character_skills.ProfessionSkill: (9, 0, 200.0),
    RobotProfession: (9, 0, 200.0),
    character_skills.Recon: (10, 0, 500.0),
    character_skills.ScienceSkill: (9, 0, 200.0),
    character_skills.Seafarer: (8, 0, 100.0),
    character_skills.Stealth: (10, 0, 500.0),
    character_skills.Steward: (8, 0, 100.0),
    character_skills.Streetwise: (13, 1, 1000.0),
    character_skills.Survival: (10, 0, 200.0),
    character_skills.Tactics: (8, 0, 100.0),
}

_DEFAULT_PROPS: tuple[int, int, float] = (8, 0, 100.0)


def _skill_props(skill: RobotSkill) -> tuple[int, int, float]:
    """Look up (tl, base_bw, base_cost) for a skill, matching subskill group keys."""
    skill_cls = type(skill)
    props = _SKILL_PACKAGE_PROPS.get(skill_cls)
    if props is not None:
        return props
    for key, props in _SKILL_PACKAGE_PROPS.items():
        if key is skill_cls:
            continue
        if key_matches_skill(key, skill_cls):
            return props
    return _DEFAULT_PROPS


def _field_characteristic(skill_cls: type[Skill], field_name: str) -> Chars | None:
    """Characteristic DM for one speciality field, or None if no robot characteristic applies."""
    key: tuple[type[Skill], str] = (skill_cls, field_name)
    if key in _NULL_SKILL_KEYS:
        return None
    if key in _STR_SKILL_KEYS:
        return Chars.STR
    if key in _INT_SKILL_KEYS:
        return Chars.INT
    if key in _DEX_SKILL_KEYS:
        return Chars.DEX
    return Chars.DEX if skill_cls in _DEX_SKILLS else Chars.INT


def skill_name(skill: RobotSkill) -> str:
    base = skill.name()
    speciality = active_speciality_label(skill)
    if speciality is None:
        return base
    return f'{base} ({speciality})'


def _specs_to_display_dict(
    per_spec: dict[tuple[type[Skill], str | None], int],
) -> dict[str, int]:
    """Compact merged per-spec levels to a display dict.

    For each skill class, if all specialities are present at the same level N > 0
    the key is 'Skill (All) N'; if all are 0 the key is 'Skill 0'; otherwise
    each non-zero spec appears individually as 'Skill (Spec) N'.
    Unspecialised entries (spec=None) produce 'Skill N'.
    """
    groups: dict[type[Skill], dict[str | None, int]] = {}
    for (skill_cls, spec), lvl in per_spec.items():
        if skill_cls not in groups:
            groups[skill_cls] = {}
        groups[skill_cls][spec] = lvl
    result: dict[str, int] = {}
    for skill_cls, spec_levels in groups.items():
        if None in spec_levels:
            result[skill_cls.name()] = spec_levels[None]
            continue
        all_specs = skill_cls.specialities()
        named = {s: lvl for s, lvl in spec_levels.items() if s is not None}
        if all_specs and set(named.keys()) == set(all_specs) and len(set(named.values())) == 1:
            lvl = next(iter(named.values()))
            if lvl == 0:
                result[skill_cls.name()] = 0
            else:
                result[f'{skill_cls.name()} (All)'] = lvl
        else:
            for spec, lvl in named.items():
                if lvl > 0:
                    result[f'{skill_cls.name()} ({spec})'] = lvl
    return result


def _skill_key(skill: RobotSkill) -> tuple[type[Skill], str | None]:
    return type(skill), active_speciality_field(skill)


def _is_dex_skill(skill: RobotSkill) -> bool:
    key = _skill_key(skill)
    if key in _INT_SKILL_KEYS:
        return False
    if key in _DEX_SKILL_KEYS:
        return True
    return type(skill) in _DEX_SKILLS


def _is_str_skill(skill: RobotSkill) -> bool:
    key = _skill_key(skill)
    return key in _STR_SKILL_KEYS


def _skill(skill_cls: type[Skill], field_name: str = 'level', value: int = 1) -> RobotSkill:
    skill = skill_cls()
    level = getattr(skill, field_name)
    level.set(value)
    return cast(RobotSkill, skill)


@dataclass(frozen=True, eq=False)
class SkillGrant:
    """A skill at a given level granted by a brain package or option."""

    name: RobotSkill
    level: int

    @property
    def name_text(self) -> str:
        return skill_name(self.name)

    def __str__(self) -> str:
        return f'{self.name_text} {self.level}'

    def __eq__(self, other) -> bool:
        if not isinstance(other, SkillGrant):
            return NotImplemented
        return self.name_text == other.name_text and self.level == other.level

    def __hash__(self) -> int:
        return hash((self.name_text, self.level))


class SkillPackage(CeresModel):
    """An installed skill package on an Advanced (or higher) robot brain."""

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    skill: RobotSkill
    # Overrides the level derived from the skill. Use for "all specialities at level N > 0"
    # (skill=Electronics(), package_level=1) or "specific speciality at level 0"
    # (skill=Athletics(strength=Level(1)), package_level=0).
    package_level: int | None = None
    # When False, grants_all_specialities() returns False even if no speciality field is active.
    # Use for skills installed as unspecialised (e.g. Gun Combat without a chosen speciality).
    expand_specialities: bool = True

    @property
    def level(self) -> int:
        """Base package level (before brain INT/DEX/STR DM)."""
        if self.package_level is not None:
            return self.package_level
        if 'level' in type(self.skill).model_fields:
            return self.skill.level.value  # type: ignore[union-attr]  # ty: ignore[unresolved-attribute]
        field = active_speciality_field(self.skill)
        return getattr(self.skill, field).value if field else 0

    @property
    def tl(self) -> int:
        return _skill_props(self.skill)[0]

    @property
    def bandwidth(self) -> int:
        return _skill_props(self.skill)[1] + self.level

    @property
    def cost(self) -> float:
        base = _skill_props(self.skill)[2]
        return base * (10.0**self.level)

    @property
    def name_text(self) -> str:
        if self.grants_all_specialities():
            return f'{self.skill.name()} (All)'
        return skill_name(self.skill)

    def grants_all_specialities(self) -> bool:
        """Speciality packages with no active speciality field grant all specialities."""
        if not self.expand_specialities:
            return False
        if 'level' in type(self.skill).model_fields:
            return False
        return active_speciality_field(self.skill) is None

    def _per_spec_entries(self, dms: dict[Chars, int]) -> list[tuple[type[Skill], str | None, int]]:
        """Raw per-field data: [(skill_cls, spec_label|None, effective_level)].

        dms maps each characteristic to its already-computed DM (0 if absent).
        spec_label is None for simple skills and expand_specialities=False packages.
        Used internally and by brain.display_labels for multi-package merging.
        For specific-speciality packages (active field is not None, no package_level),
        only fields with raw level > 0 are included — uninstalled specs are omitted.
        """
        skill_cls = type(self.skill)
        if not skill_cls.specialities():
            char = Chars.STR if _is_str_skill(self.skill) else (Chars.DEX if _is_dex_skill(self.skill) else Chars.INT)
            return [(skill_cls, None, max(0, self.level + dms.get(char, 0)))]
        if not self.expand_specialities:
            char = Chars.DEX if _is_dex_skill(self.skill) else Chars.INT
            return [(skill_cls, None, max(0, self.level + dms.get(char, 0)))]
        pkg_level = self.package_level
        active_field = active_speciality_field(self.skill)
        result: list[tuple[type[Skill], str | None, int]] = []
        for field_name in level_fields(skill_cls):
            char = _field_characteristic(skill_cls, field_name)
            if char is None:
                continue
            if pkg_level is not None:
                raw = pkg_level if (active_field is None or field_name == active_field) else 0
            else:
                raw = getattr(self.skill, field_name).value
            spec = speciality_label(self.skill, field_name)
            result.append((skill_cls, spec, max(0, raw + dms.get(char, 0))))
        return result

    def display_labels(self, dms: dict[Chars, int]) -> list[str]:
        """Effective skill labels given the robot's characteristic DMs."""
        entries = self._per_spec_entries(dms)
        if not entries:
            return []
        per_spec = {(cls, spec): lvl for cls, spec, lvl in entries}
        display = _specs_to_display_dict(per_spec)
        return [f'{k} {v}' for k, v in display.items()]


_PRIMITIVE_SKILLS: dict[str, tuple[SkillGrant, ...]] = {
    'alert': (SkillGrant(_skill(character_skills.Recon), 0),),
    'clean': (SkillGrant(_skill(RobotProfession, 'domestic_cleaner'), 2),),
    'evade': (
        SkillGrant(_skill(character_skills.Athletics, 'dexterity'), 1),
        SkillGrant(_skill(character_skills.Stealth), 2),
    ),
    'homing': (SkillGrant(_skill(Weapon), 1),),
    'labourer': (SkillGrant(_skill(RobotProfession, 'labourer'), 2),),
    'locomotion': (SkillGrant(_skill(character_skills.Athletics, 'dexterity'), 1),),
    'none': (),
    'recon': (
        SkillGrant(_skill(character_skills.Recon), 2),
        SkillGrant(_skill(character_skills.Athletics, 'dexterity'), 1),
    ),
    'servant': (SkillGrant(_skill(RobotProfession, 'domestic_servant'), 2),),
}


def primitive_package_skills(function: str) -> tuple[SkillGrant, ...]:
    return _PRIMITIVE_SKILLS.get(function, ())


class BrainSoftware(CeresModel):
    """Non-skill software installed in an Advanced (or higher) brain, consuming bandwidth.

    Used for software packages such as Universal Translator that run on the brain
    and consume bandwidth but do not grant skills.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    bandwidth: int
    tl: int = 0
    cost: float = 0.0

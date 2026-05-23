"""Skill grants and installed skill packages for robot brains."""

from dataclasses import dataclass
from typing import Annotated, Literal, cast, get_args, get_origin

from pydantic import Field

from ceres.character import skills as character_skills
from ceres.character.skills import AnySkill, Level, Skill
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


class Zoology(Skill):
    type: Literal['Robot Zoology'] = 'Robot Zoology'
    level: Level = _level()

    @classmethod
    def name(cls) -> str:
        return 'Zoology'


type RobotSpecificSkill = Annotated[RobotProfession | Weapon | Zoology, Field(discriminator='type')]
type RobotSkill = AnySkill | RobotSpecificSkill
type _SkillCostKey = object


def _skill_classes_from_key(key: _SkillCostKey) -> tuple[type[Skill], ...]:
    if hasattr(key, '__value__'):
        key = key.__value__
    if get_origin(key) is Annotated:
        key = get_args(key)[0]
    if isinstance(key, type) and issubclass(key, Skill):
        return (key,)
    return tuple(arg for arg in get_args(key) if isinstance(arg, type) and issubclass(arg, Skill))


def _key_matches_skill(key: _SkillCostKey, skill_cls: type[Skill]) -> bool:
    return skill_cls in _skill_classes_from_key(key)


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

_DEX_SKILL_KEYS: frozenset[tuple[type[Skill], str | None]] = frozenset({(character_skills.Athletics, 'dexterity')})

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

_DEX_SKILL_KEYS: frozenset[tuple[type[Skill], str | None]] = _DEX_SKILL_KEYS | frozenset(
    {
        (character_skills.Gunner, 'screen'),
        (character_skills.Gunner, 'turret'),
        (character_skills.Pilot, 'small_craft'),
        (character_skills.Pilot, 'spacecraft'),
    }
)

# Base costs (level 0) per refs/robot/35_skill_packages.md Standard Skill Packages table.
# Cost at level N = base × 10^N.
_SKILL_BASE_COSTS: dict[_SkillCostKey, float] = {
    character_skills.Admin: 100.0,
    character_skills.Advocate: 500.0,
    character_skills.Animals: 200.0,
    character_skills.ArtSkill: 500.0,
    character_skills.Astrogation: 500.0,
    character_skills.Athletics: 100.0,
    character_skills.Broker: 200.0,
    character_skills.Carouse: 500.0,
    character_skills.Deception: 1000.0,
    character_skills.Diplomat: 500.0,
    character_skills.Drive: 100.0,
    character_skills.Electronics: 100.0,
    character_skills.Engineer: 200.0,
    character_skills.Explosives: 100.0,
    character_skills.Flyer: 100.0,
    character_skills.Gambler: 500.0,
    character_skills.GunCombat: 100.0,
    character_skills.Gunner: 100.0,
    character_skills.HeavyWeapons: 100.0,
    character_skills.Investigate: 500.0,
    character_skills.Languages: 200.0,
    character_skills.Leadership: 1000.0,
    character_skills.Mechanic: 100.0,
    character_skills.Medic: 200.0,
    character_skills.Melee: 100.0,
    character_skills.Navigation: 100.0,
    character_skills.Persuade: 500.0,
    character_skills.Pilot: 100.0,
    character_skills.ProfessionSkill: 200.0,
    RobotProfession: 200.0,
    character_skills.Recon: 500.0,
    character_skills.ScienceSkill: 200.0,
    character_skills.Seafarer: 100.0,
    character_skills.Stealth: 500.0,
    character_skills.Steward: 100.0,
    character_skills.Streetwise: 1000.0,
    character_skills.Survival: 200.0,
    character_skills.Tactics: 100.0,
}


def _skill_base_cost(skill: RobotSkill) -> float:
    skill_cls = type(skill)
    cost = _SKILL_BASE_COSTS.get(skill_cls)
    if cost is not None:
        return cost
    for key, cost in _SKILL_BASE_COSTS.items():
        if key is skill_cls:
            continue
        if _key_matches_skill(key, skill_cls):
            return cost
    return 100.0


def _speciality_label(skill: Skill, field_name: str) -> str:
    field = type(skill).model_fields[field_name]
    extra = field.json_schema_extra or {}
    return str(extra.get('name') or field_name.replace('_', ' ').title())


def _active_speciality_field(skill: Skill) -> str | None:
    if 'level' in type(skill).model_fields:
        return None
    active: list[str] = []
    for field_name, field in type(skill).model_fields.items():
        if field_name in {'display_label', 'type'} or field.annotation is not Level:
            continue
        level = getattr(skill, field_name)
        if isinstance(level, Level) and level.value > 0:
            active.append(field_name)
    if len(active) == 1:
        return active[0]
    return None


def _active_speciality_label(skill: Skill) -> str | None:
    field_name = _active_speciality_field(skill)
    if field_name is None:
        return None
    return _speciality_label(skill, field_name)


def skill_name(skill: RobotSkill) -> str:
    base = skill.name()
    speciality = _active_speciality_label(skill)
    if speciality is None:
        return base
    return f'{base} ({speciality})'


def _base_skill_name(skill: RobotSkill) -> str:
    if isinstance(
        skill,
        (
            character_skills.PerformingArt,
            character_skills.CreativeArt,
            character_skills.PresentationArt,
        ),
    ):
        return 'Art'
    if isinstance(
        skill,
        (
            character_skills.ColonistProfession,
            character_skills.CrewmemberProfession,
            character_skills.FreeloaderProfession,
            character_skills.HostileEnvironmentProfession,
            character_skills.SpacerProfession,
            character_skills.SportProfession,
            character_skills.WorkerProfession,
        ),
    ):
        return 'Profession'
    if isinstance(
        skill,
        (
            character_skills.LifeScience,
            character_skills.PhysicalScience,
            character_skills.RoboticScience,
            character_skills.SocialScience,
            character_skills.SpaceScience,
        ),
    ):
        return 'Science'
    if isinstance(
        skill,
        (
            character_skills.LanguageGalanglic,
            character_skills.LanguageVilani,
            character_skills.LanguageZdetl,
            character_skills.LanguageOynprith,
            character_skills.LanguageTrokh,
            character_skills.LanguageGvegh,
        ),
    ):
        return 'Language'
    return skill.name()


def _skill_key(skill: RobotSkill) -> tuple[type[Skill], str | None]:
    return type(skill), _active_speciality_field(skill)


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
    all_specialities: bool = False

    @property
    def name_text(self) -> str:
        if self.all_specialities:
            return f'{_base_skill_name(self.name)} (All)'
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

    model_config = {'frozen': True}

    name: RobotSkill
    level: int
    bandwidth: int
    all_specialities: bool = False

    @property
    def name_text(self) -> str:
        if self.all_specialities:
            return f'{self.base_name} (All)'
        return skill_name(self.name)

    @property
    def base_name(self) -> str:
        return _base_skill_name(self.name)

    def grants_all_specialities(self) -> bool:
        """Level-0 speciality packages grant all specialities, not one named speciality."""
        return self.all_specialities or (self.level == 0 and _active_speciality_field(self.name) is not None)

    def skill_grant(self, level: int, *, exact_speciality: bool = False) -> SkillGrant:
        return SkillGrant(
            self.name,
            level,
            all_specialities=(not exact_speciality and self.grants_all_specialities()),
        )

    @property
    def uses_dex_dm(self) -> bool:
        return _is_dex_skill(self.name)

    @property
    def uses_str_dm(self) -> bool:
        return _is_str_skill(self.name)

    @property
    def uses_exact_speciality_dm(self) -> bool:
        key = _skill_key(self.name)
        return key in _DEX_SKILL_KEYS or key in _STR_SKILL_KEYS

    @property
    def cost(self) -> float:
        base = _skill_base_cost(self.name)
        return base * (10.0**self.level)


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

    model_config = {'frozen': True}

    name: str
    bandwidth: int
    tl: int = 0
    cost: float = 0.0


__all__ = [
    SkillGrant,
    SkillPackage,
    BrainSoftware,
    RobotProfession,
    Weapon,
    Zoology,
    primitive_package_skills,
    _DEX_SKILLS,
]

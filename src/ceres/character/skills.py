from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, Final, Literal, NamedTuple, Self, cast, get_args, get_origin

if TYPE_CHECKING:
    from ceres.character.state import CharacterSummary

from pydantic import Field

from ceres.shared import CeresModel


class Level(CeresModel):
    value: int = 0

    def set(self, value: int) -> None:
        self.value = value

    def __iadd__(self, amount: int) -> Self:
        self.value += amount
        return self

    def __int__(self) -> int:
        return self.value


def _level(name: str | None = None):
    return Field(default_factory=Level, json_schema_extra={'name': name} if name else None)


class Skill(CeresModel):
    @classmethod
    def name(cls) -> str:
        return get_args(cls.model_fields['type'].annotation)[0]

    @classmethod
    def specialities(cls) -> tuple[str, ...]:
        names: list[str] = []
        for field_name, field in cls.model_fields.items():
            if field_name in {'display_label', 'type', 'level'} or field.annotation is not Level:
                continue
            extra = field.json_schema_extra or {}
            names.append(str(extra.get('name') or field_name.replace('_', ' ').title()))
        return tuple(names)

    def __str__(self) -> str:
        fields = _level_fields(type(self))
        if len(fields) == 1 and fields[0] == 'level':
            lvl = cast(Level, getattr(self, fields[0]))
            return f'{type(self).name()}-{lvl.value}'
        active: list[str] = []
        for field_name, field in type(self).model_fields.items():
            if field_name in {'display_label', 'type'} or field.annotation is not Level:
                continue
            lvl = getattr(self, field_name)
            if isinstance(lvl, Level) and lvl.value > 0:
                extra = field.json_schema_extra or {}
                label = str(extra.get('name') or field_name.replace('_', ' ').title())
                active.append(f'{type(self).name()} ({label})-{lvl.value}')
        if active:
            return ', '.join(active)
        return f'{type(self).name()}-0'


class Admin(Skill):
    type: Literal['Admin'] = 'Admin'
    level: Level = _level()


class Advocate(Skill):
    type: Literal['Advocate'] = 'Advocate'
    level: Level = _level()


class Animals(Skill):
    type: Literal['Animals'] = 'Animals'
    handling: Level = _level('Handling')
    veterinary: Level = _level('Veterinary')
    training: Level = _level('Training')


class PerformingArt(Skill):
    type: Literal['Performing Art'] = 'Performing Art'
    performer: Level = _level('Performer')
    instrument: Level = _level('Instrument')


class CreativeArt(Skill):
    type: Literal['Creative Art'] = 'Creative Art'
    visual_media: Level = _level('Visual Media')
    exotic_media: Level = _level('Exotic Media')


class PresentationArt(Skill):
    type: Literal['Presentation Art'] = 'Presentation Art'
    holography: Level = _level('Holography')
    writing: Level = _level('Writing')


class Astrogation(Skill):
    type: Literal['Astrogation'] = 'Astrogation'
    level: Level = _level()


class Athletics(Skill):
    type: Literal['Athletics'] = 'Athletics'
    dexterity: Level = _level('Dexterity')
    endurance: Level = _level('Endurance')
    strength: Level = _level('Strength')


class Broker(Skill):
    type: Literal['Broker'] = 'Broker'
    level: Level = _level()


class Carouse(Skill):
    type: Literal['Carouse'] = 'Carouse'
    level: Level = _level()


class Deception(Skill):
    type: Literal['Deception'] = 'Deception'
    level: Level = _level()


class Diplomat(Skill):
    type: Literal['Diplomat'] = 'Diplomat'
    level: Level = _level()


class Drive(Skill):
    type: Literal['Drive'] = 'Drive'
    hovercraft: Level = _level('Hovercraft')
    mole: Level = _level('Mole')
    track: Level = _level('Track')
    walker: Level = _level('Walker')
    wheel: Level = _level('Wheel')


class Electronics(Skill):
    type: Literal['Electronics'] = 'Electronics'
    comms: Level = _level('Comms')
    computers: Level = _level('Computers')
    remote_ops: Level = _level('Remote Ops')
    sensors: Level = _level('Sensors')


class Engineer(Skill):
    type: Literal['Engineer'] = 'Engineer'
    m_drive: Level = _level('M-drive')
    j_drive: Level = _level('J-drive')
    life_support: Level = _level('Life Support')
    power: Level = _level('Power')


class Explosives(Skill):
    type: Literal['Explosives'] = 'Explosives'
    level: Level = _level()


class Flyer(Skill):
    type: Literal['Flyer'] = 'Flyer'
    airship: Level = _level('Airship')
    grav: Level = _level('Grav')
    ornithopter: Level = _level('Ornithopter')
    rotor: Level = _level('Rotor')
    wing: Level = _level('Wing')


class Gambler(Skill):
    type: Literal['Gambler'] = 'Gambler'
    level: Level = _level()


class GunCombat(Skill):
    type: Literal['Gun Combat'] = 'Gun Combat'
    archaic: Level = _level('Archaic')
    energy: Level = _level('Energy')
    slug: Level = _level('Slug')


class Gunner(Skill):
    type: Literal['Gunner'] = 'Gunner'
    turret: Level = _level('Turret')
    ortillery: Level = _level('Ortillery')
    screen: Level = _level('Screen')
    capital: Level = _level('Capital')


class HeavyWeapons(Skill):
    type: Literal['Heavy Weapons'] = 'Heavy Weapons'
    artillery: Level = _level('Artillery')
    portable: Level = _level('Portable')
    vehicle: Level = _level('Vehicle')


class Investigate(Skill):
    type: Literal['Investigate'] = 'Investigate'
    level: Level = _level()


class JackOfAllTrades(Skill):
    type: Literal['Jack-of-All-Trades'] = 'Jack-of-All-Trades'
    level: Level = _level()


class LanguageGalanglic(Skill):
    type: Literal['Language Galanglic'] = 'Language Galanglic'
    level: Level = _level()


class LanguageVilani(Skill):
    type: Literal['Language Vilani'] = 'Language Vilani'
    level: Level = _level()


class LanguageZdetl(Skill):
    type: Literal['Language Zdetl'] = 'Language Zdetl'
    level: Level = _level()


class LanguageOynprith(Skill):
    type: Literal['Language Oynprith'] = 'Language Oynprith'
    level: Level = _level()


class LanguageTrokh(Skill):
    type: Literal['Language Trokh'] = 'Language Trokh'
    level: Level = _level()


class LanguageGvegh(Skill):
    type: Literal['Language Gvegh'] = 'Language Gvegh'
    level: Level = _level()


class Leadership(Skill):
    type: Literal['Leadership'] = 'Leadership'
    level: Level = _level()


class Mechanic(Skill):
    type: Literal['Mechanic'] = 'Mechanic'
    level: Level = _level()


class Medic(Skill):
    type: Literal['Medic'] = 'Medic'
    level: Level = _level()


class Melee(Skill):
    type: Literal['Melee'] = 'Melee'
    unarmed: Level = _level('Unarmed')
    blade: Level = _level('Blade')
    bludgeon: Level = _level('Bludgeon')
    natural: Level = _level('Natural')
    grapple: Level = _level('Grapple')
    striking: Level = _level('Striking')
    fencing: Level = _level('Fencing')


class Navigation(Skill):
    type: Literal['Navigation'] = 'Navigation'
    level: Level = _level()


class Persuade(Skill):
    type: Literal['Persuade'] = 'Persuade'
    level: Level = _level()


class Pilot(Skill):
    type: Literal['Pilot'] = 'Pilot'
    small_craft: Level = _level('Small Craft')
    spacecraft: Level = _level('Spacecraft')
    capital_ships: Level = _level('Capital Ships')


class ColonistProfession(Skill):
    type: Literal['Colonist Profession'] = 'Colonist Profession'
    farming: Level = _level('Farming')
    ranching: Level = _level('Ranching')


class FreeloaderProfession(Skill):
    type: Literal['Freeloader Profession'] = 'Freeloader Profession'
    scrounging: Level = _level('Scrounging')
    security: Level = _level('Security')


class HostileEnvironmentProfession(Skill):
    type: Literal['Hostile Environment Profession'] = 'Hostile Environment Profession'
    contaminant: Level = _level('Contaminant')
    low_g: Level = _level('Low-G')
    high_g: Level = _level('High-G')
    underwater: Level = _level('Underwater')


class SpacerProfession(Skill):
    type: Literal['Spacer Profession'] = 'Spacer Profession'
    belter: Level = _level('Belter')
    crewmember: Level = _level('Crewmember')


class SportProfession(Skill):
    type: Literal['Sport Profession'] = 'Sport Profession'
    atmosphere_surfing: Level = _level('Atmosphere Surfing')
    golf: Level = _level('Golf')
    motorsports: Level = _level('Motorsports')
    racquet_sports: Level = _level('Racquet Sports')
    team_ball_sports: Level = _level('Team Ball Sports')
    track_and_field: Level = _level('Track & Field')


class WorkerProfession(Skill):
    type: Literal['Worker Profession'] = 'Worker Profession'
    armourer: Level = _level('Armourer')
    biologicals: Level = _level('Biologicals')
    civil_engineering: Level = _level('Civil Engineering')
    construction: Level = _level('Construction')
    hydroponics: Level = _level('Hydroponics')
    metalworking: Level = _level('Metalworking')
    polymers: Level = _level('Polymers')


class Recon(Skill):
    type: Literal['Recon'] = 'Recon'
    level: Level = _level()


class LifeScience(Skill):
    type: Literal['Life Science'] = 'Life Science'
    biology: Level = _level('Biology')
    genetics: Level = _level('Genetics')
    psionicology: Level = _level('Psionicology')
    xenology: Level = _level('Xenology')


class PhysicalScience(Skill):
    type: Literal['Physical Science'] = 'Physical Science'
    chemistry: Level = _level('Chemistry')
    physics: Level = _level('Physics')
    jumpspace_physics: Level = _level('Jumpspace Physics')


class RoboticScience(Skill):
    type: Literal['Robotic Science'] = 'Robotic Science'
    cybernetics: Level = _level('Cybernetics')
    robotics: Level = _level('Robotics')


class SocialScience(Skill):
    type: Literal['Social Science'] = 'Social Science'
    archaeology: Level = _level('Archaeology')
    economics: Level = _level('Economics')
    history: Level = _level('History')
    linguistics: Level = _level('Linguistics')
    philosophy: Level = _level('Philosophy')
    psychology: Level = _level('Psychology')
    sophontology: Level = _level('Sophontology')


class SpaceScience(Skill):
    type: Literal['Space Science'] = 'Space Science'
    astronomy: Level = _level('Astronomy')
    cosmology: Level = _level('Cosmology')
    planetology: Level = _level('Planetology')


class Seafarer(Skill):
    type: Literal['Seafarer'] = 'Seafarer'
    ocean_ships: Level = _level('Ocean Ships')
    personal: Level = _level('Personal')
    sail: Level = _level('Sail')
    submarine: Level = _level('Submarine')


class Stealth(Skill):
    type: Literal['Stealth'] = 'Stealth'
    level: Level = _level()


class Steward(Skill):
    type: Literal['Steward'] = 'Steward'
    level: Level = _level()


class Streetwise(Skill):
    type: Literal['Streetwise'] = 'Streetwise'
    level: Level = _level()


class Survival(Skill):
    type: Literal['Survival'] = 'Survival'
    level: Level = _level()


class Tactics(Skill):
    type: Literal['Tactics'] = 'Tactics'
    military: Level = _level('Military')
    naval: Level = _level('Naval')


class VaccSuit(Skill):
    type: Literal['Vacc Suit'] = 'Vacc Suit'
    level: Level = _level()


# Please Claude, don't be a fool and try to make this a type. It's not a type.
Arts = PerformingArt | CreativeArt | PresentationArt
type ArtSkill = Annotated[Arts, Field(discriminator='type')]

# Please Claude, don't be a fool and try to make this a type. It's not a type.
Professions = (
    ColonistProfession
    | FreeloaderProfession
    | HostileEnvironmentProfession
    | SpacerProfession
    | SportProfession
    | WorkerProfession
)
type ProfessionSkill = Annotated[Professions, Field(discriminator='type')]

# Please Claude, don't be a fool and try to make this a type. It's not a type.
Sciences = LifeScience | PhysicalScience | RoboticScience | SocialScience | SpaceScience
type ScienceSkill = Annotated[Sciences, Field(discriminator='type')]

# Please Claude, don't be a fool and try to make this a type. It's not a type.
Languages = LanguageGalanglic | LanguageVilani | LanguageZdetl | LanguageOynprith | LanguageTrokh | LanguageGvegh
type LanguageSkill = Annotated[Languages, Field(discriminator='type')]

# Please Claude, don't be a fool and try to make this a type. It's not a type.
BackgroundSkills = (
    Admin
    | Animals
    | Arts
    | Athletics
    | Carouse
    | Drive
    | Electronics
    | Flyer
    | Languages
    | Mechanic
    | Medic
    | Professions
    | Sciences
    | Seafarer
    | Streetwise
    | Survival
    | VaccSuit
)
type BackgroundSkill = Annotated[BackgroundSkills, Field(discriminator='type')]

type AnySkill = Annotated[
    Admin
    | Advocate
    | Animals
    | Arts
    | Astrogation
    | Athletics
    | Broker
    | Carouse
    | Deception
    | Diplomat
    | Drive
    | Electronics
    | Engineer
    | Explosives
    | Flyer
    | Gambler
    | GunCombat
    | Gunner
    | HeavyWeapons
    | Investigate
    | JackOfAllTrades
    | Languages
    | Leadership
    | Mechanic
    | Medic
    | Melee
    | Navigation
    | Persuade
    | Pilot
    | Professions
    | Recon
    | Sciences
    | Seafarer
    | Stealth
    | Steward
    | Streetwise
    | Survival
    | Tactics
    | VaccSuit,
    Field(discriminator='type'),
]


class SkillInfo(NamedTuple):
    type: str
    specialities: tuple[str, ...] = ()


def _skill_classes(skill_union: object) -> tuple[type[Skill], ...]:
    if hasattr(skill_union, '__value__'):
        skill_union = skill_union.__value__
    if get_origin(skill_union) is Annotated:
        skill_union = get_args(skill_union)[0]
    return get_args(skill_union)


def skill_list(skill_union: object = AnySkill) -> tuple[SkillInfo, ...]:
    return tuple(SkillInfo(skill.name(), skill.specialities()) for skill in _skill_classes(skill_union))


def skill_names(skill_union: object) -> list[str]:
    return [cls.name() for cls in _skill_classes(skill_union)]


def skill_instances(skill_union: object) -> list[AnySkill]:
    return [cast(AnySkill, cls()) for cls in _skill_classes(skill_union)]


def skill_spec_option_names(skill_name: str) -> list[str]:
    """Return one option label per specialisation for specialised skills, or [skill_name] for unspecialised."""
    cls = skill_class_by_name(skill_name)
    specs = cls.specialities()
    if not specs:
        return [skill_name]
    return [f'{skill_name} ({spec})' for spec in specs]


def parse_skill_spec_option(option: str) -> tuple[str, str | None]:
    """Parse 'Skill (Spec)' into (skill_name, spec_name), or 'Skill' into (skill_name, None)."""
    if option.endswith(')') and ' (' in option:
        idx = option.rfind(' (')
        return option[:idx], option[idx + 2 : -1]
    return option, None


def _level_fields(skill_cls: type[Skill]) -> list[str]:
    return [
        name
        for name, field in skill_cls.model_fields.items()
        if name not in {'type', 'display_label'} and field.annotation is Level
    ]


def skill_class_by_name(name: str) -> type[Skill]:
    for cls in _skill_classes(AnySkill):
        if cls.name() == name:
            return cls
    raise ValueError(f'Unknown skill: {name!r}')


def field_for_spec(cls: type[Skill], spec: str) -> str:
    """Return the field name for a specialisation display name (e.g. 'Computers' → 'computers')."""
    for field_name, field in cls.model_fields.items():
        if field_name in {'display_label', 'type'}:
            continue
        extra = field.json_schema_extra or {}
        label = str(extra.get('name') or field_name.replace('_', ' ').title())
        if label.lower() == spec.lower():
            return field_name
    raise ValueError(f'Unknown specialisation {spec!r} for skill {cls.name()!r}')


def skill_from_str(name: str, level: int = 0) -> AnySkill:
    """Create a skill instance from a string name and level."""

    skill_cls = skill_class_by_name(name)
    _cls: Any = skill_cls
    if level == 0:
        return cast(AnySkill, _cls())
    if not _cls().specialities():
        return cast(AnySkill, _cls(level=Level(value=level)))
    fields = {f: Level(value=level) for f in _level_fields(skill_cls)}
    return cast(AnySkill, _cls(**fields))


def expand_to_spec_options(skill_name: str) -> list[str]:
    """For a specialised skill, return 'Skill (Spec)' for every specialisation.

    For plain (non-specialised) skills, returns [skill_name] unchanged.
    Use this when presenting level > 0 choices: specialised skills must be chosen
    at the specialisation level, never as a bare name.
    """
    try:
        cls = skill_class_by_name(skill_name)
    except ValueError:
        return [skill_name]
    specs = cls.specialities()
    return [f'{skill_name} ({spec})' for spec in specs] if specs else [skill_name]


def speciality_label(skill: Skill, field_name: str) -> str:
    field = type(skill).model_fields[field_name]
    extra = field.json_schema_extra or {}
    return str(extra.get('name') or field_name.replace('_', ' ').title())


def active_speciality_field(skill: Skill) -> str | None:
    if 'level' in type(skill).model_fields:
        return None
    active: list[str] = []
    for field_name, field in type(skill).model_fields.items():
        if field_name in {'display_label', 'type'} or field.annotation is not Level:
            continue
        lvl = getattr(skill, field_name)
        if isinstance(lvl, Level) and lvl.value > 0:
            active.append(field_name)
    if len(active) == 1:
        return active[0]
    return None


def active_speciality_label(skill: Skill) -> str | None:
    field_name = active_speciality_field(skill)
    if field_name is None:
        return None
    return speciality_label(skill, field_name)


@dataclass(frozen=True)
class SkillSpecialization:
    """Targets one specific specialisation of a specialised skill."""

    skill_cls: type[Skill]
    spec: str  # display name, e.g. 'Slug' for GunCombat

    def __post_init__(self) -> None:
        field_for_spec(self.skill_cls, self.spec)  # raises ValueError if invalid


def skill_spec(cls: type[Skill], spec: str) -> SkillSpecialization:
    """Validated factory for SkillSpecialization. Raises ValueError for unknown specs."""
    return SkillSpecialization(cls, spec)


class _ExistingSkillsSentinel:
    """Sentinel: expand to increment every skill the character currently has."""


EXISTING_SKILLS: Final[_ExistingSkillsSentinel] = _ExistingSkillsSentinel()


def _to_skill_classes(spec: object) -> tuple[type[Skill], ...]:
    if isinstance(spec, type) and issubclass(spec, Skill):
        return (spec,)
    return _skill_classes(spec)


def _gain_from_class(
    cls: type[Skill],
    spec_name: str | None,
    level: int | None,
    existing: AnySkill | None,
) -> list[AnySkill]:
    fields = _level_fields(cls)
    is_specialised = not (len(fields) == 1 and fields[0] == 'level')
    _cls: Any = cls

    if level == 0:
        if existing is None:
            return [cast(AnySkill, _cls())]
        return []

    if not is_specialised:
        current = cast(Level, getattr(existing, fields[0])).value if existing is not None else 0
        new_level = (current + 1) if level is None else level
        if new_level > current and new_level <= 4:
            return [cast(AnySkill, _cls(level=Level(value=new_level)))]
        return []

    target_fields = [field_for_spec(cls, spec_name)] if spec_name is not None else fields
    results: list[AnySkill] = []
    for field in target_fields:
        current = getattr(existing, field).value if existing is not None else 0
        new_level = (current + 1) if level is None else level
        if new_level > current and new_level <= 4:
            results.append(cast(AnySkill, _cls(**{field: Level(value=new_level)})))
    return results


def gain_skills(
    summary: CharacterSummary,
    spec: object,
    level: int | None = None,
) -> list[AnySkill]:
    """Return possible skill improvements for the given spec and level target."""
    if isinstance(spec, _ExistingSkillsSentinel):
        if level is not None:
            raise ValueError('EXISTING_SKILLS requires level=None')
        results: list[AnySkill] = []
        for existing_skill in summary.skills:
            results.extend(_gain_from_class(type(existing_skill), None, None, existing_skill))
        return results

    if isinstance(spec, SkillSpecialization):
        cls = spec.skill_cls
        existing = next((s for s in summary.skills if type(s) is cls), None)
        spec_name = None if level == 0 else spec.spec
        return _gain_from_class(cls, spec_name, level, existing)

    classes = _to_skill_classes(spec)
    results = []
    for cls in classes:
        existing = next((s for s in summary.skills if type(s) is cls), None)
        results.extend(_gain_from_class(cls, None, level, existing))
    return results

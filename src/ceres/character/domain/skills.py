from typing import Annotated, Literal, Self, cast, get_args, get_origin

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
        raw = get_args(cls.model_fields['kind'].annotation)[0]
        return raw.replace('_', ' ').title()

    @classmethod
    def specialities(cls) -> tuple[str, ...]:
        names: list[str] = []
        for field_name, field in cls.model_fields.items():
            if field_name in {'display_label', 'kind', 'level'} or field.annotation is not Level:
                continue
            extra = field.json_schema_extra or {}
            names.append(str(extra.get('name') or field_name.replace('_', ' ').title()))
        return tuple(names)


class Admin(Skill):
    kind: Literal['ADMIN'] = 'ADMIN'
    level: Level = _level()


class Advocate(Skill):
    kind: Literal['ADVOCATE'] = 'ADVOCATE'
    level: Level = _level()


class Animals(Skill):
    kind: Literal['ANIMALS'] = 'ANIMALS'
    handling: Level = _level('Handling')
    veterinary: Level = _level('Veterinary')
    training: Level = _level('Training')


class PerformingArt(Skill):
    kind: Literal['PERFORMING_ART'] = 'PERFORMING_ART'
    performer: Level = _level('Performer')
    instrument: Level = _level('Instrument')


class CreativeArt(Skill):
    kind: Literal['CREATIVE_ART'] = 'CREATIVE_ART'
    visual_media: Level = _level('Visual Media')
    exotic_media: Level = _level('Exotic Media')


class PresentationArt(Skill):
    kind: Literal['PRESENTATION_ART'] = 'PRESENTATION_ART'
    holography: Level = _level('Holography')
    writing: Level = _level('Writing')


class Astrogation(Skill):
    kind: Literal['ASTROGATION'] = 'ASTROGATION'
    level: Level = _level()


class Athletics(Skill):
    kind: Literal['ATHLETICS'] = 'ATHLETICS'
    dexterity: Level = _level('Dexterity')
    endurance: Level = _level('Endurance')
    strength: Level = _level('Strength')


class Broker(Skill):
    kind: Literal['BROKER'] = 'BROKER'
    level: Level = _level()


class Carouse(Skill):
    kind: Literal['CAROUSE'] = 'CAROUSE'
    level: Level = _level()


class Deception(Skill):
    kind: Literal['DECEPTION'] = 'DECEPTION'
    level: Level = _level()


class Diplomat(Skill):
    kind: Literal['DIPLOMAT'] = 'DIPLOMAT'
    level: Level = _level()


class Drive(Skill):
    kind: Literal['DRIVE'] = 'DRIVE'
    hovercraft: Level = _level('Hovercraft')
    mole: Level = _level('Mole')
    track: Level = _level('Track')
    walker: Level = _level('Walker')
    wheel: Level = _level('Wheel')


class Electronics(Skill):
    kind: Literal['ELECTRONICS'] = 'ELECTRONICS'
    comms: Level = _level('Comms')
    computers: Level = _level('Computers')
    remote_ops: Level = _level('Remote Ops')
    sensors: Level = _level('Sensors')


class Engineer(Skill):
    kind: Literal['ENGINEER'] = 'ENGINEER'
    m_drive: Level = _level('M-Drive')
    j_drive: Level = _level('J-Drive')
    life_support: Level = _level('Life Support')
    power: Level = _level('Power')


class Explosives(Skill):
    kind: Literal['EXPLOSIVES'] = 'EXPLOSIVES'
    level: Level = _level()


class Flyer(Skill):
    kind: Literal['FLYER'] = 'FLYER'
    airship: Level = _level('Airship')
    grav: Level = _level('Grav')
    ornithopter: Level = _level('Ornithopter')
    rotor: Level = _level('Rotor')
    wing: Level = _level('Wing')


class Gambler(Skill):
    kind: Literal['GAMBLER'] = 'GAMBLER'
    level: Level = _level()


class GunCombat(Skill):
    kind: Literal['GUN_COMBAT'] = 'GUN_COMBAT'
    archaic: Level = _level('Archaic')
    energy: Level = _level('Energy')
    slug: Level = _level('Slug')


class Gunner(Skill):
    kind: Literal['GUNNER'] = 'GUNNER'
    turret: Level = _level('Turret')
    ortillery: Level = _level('Ortillery')
    screen: Level = _level('Screen')
    capital: Level = _level('Capital')


class HeavyWeapons(Skill):
    kind: Literal['HEAVY_WEAPONS'] = 'HEAVY_WEAPONS'
    artillery: Level = _level('Artillery')
    portable: Level = _level('Portable')
    vehicle: Level = _level('Vehicle')


class Investigate(Skill):
    kind: Literal['INVESTIGATE'] = 'INVESTIGATE'
    level: Level = _level()


class JackOfAllTrades(Skill):
    kind: Literal['JACK_OF_ALL_TRADES'] = 'JACK_OF_ALL_TRADES'
    level: Level = _level()

    @classmethod
    def name(cls) -> str:
        return 'Jack-of-All-Trades'


class LanguageGalanglic(Skill):
    kind: Literal['LANGUAGE_GALANGLIC'] = 'LANGUAGE_GALANGLIC'
    level: Level = _level()


class LanguageVilani(Skill):
    kind: Literal['LANGUAGE_VILANI'] = 'LANGUAGE_VILANI'
    level: Level = _level()

    @classmethod
    def name(cls) -> str:
        return 'Language Bilanidin'


class LanguageZdetl(Skill):
    kind: Literal['LANGUAGE_ZDETL'] = 'LANGUAGE_ZDETL'
    level: Level = _level()


class LanguageOynprith(Skill):
    kind: Literal['LANGUAGE_OYNPRITH'] = 'LANGUAGE_OYNPRITH'
    level: Level = _level()


class LanguageTrokh(Skill):
    kind: Literal['LANGUAGE_TROKH'] = 'LANGUAGE_TROKH'
    level: Level = _level()


class LanguageGvegh(Skill):
    kind: Literal['LANGUAGE_GVEGH'] = 'LANGUAGE_GVEGH'
    level: Level = _level()


class LanguageAekhu(Skill):
    kind: Literal['LANGUAGE_AEKHU'] = 'LANGUAGE_AEKHU'
    level: Level = _level()


class LanguageArrghoun(Skill):
    kind: Literal['LANGUAGE_ARRGHOUN'] = 'LANGUAGE_ARRGHOUN'
    level: Level = _level()


class LanguageIrilitok(Skill):
    kind: Literal['LANGUAGE_IRILITOK'] = 'LANGUAGE_IRILITOK'
    level: Level = _level()


class LanguageLogaksu(Skill):
    kind: Literal['LANGUAGE_LOGAKSU'] = 'LANGUAGE_LOGAKSU'
    level: Level = _level()


class LanguageOvaghoun(Skill):
    kind: Literal['LANGUAGE_OVAGHOUN'] = 'LANGUAGE_OVAGHOUN'
    level: Level = _level()


class LanguageSuedzuk(Skill):
    kind: Literal['LANGUAGE_SUEDZUK'] = 'LANGUAGE_SUEDZUK'
    level: Level = _level()


class LanguageVuakedh(Skill):
    kind: Literal['LANGUAGE_VUAKEDH'] = 'LANGUAGE_VUAKEDH'
    level: Level = _level()


class LanguageSagamaal(Skill):
    kind: Literal['LANGUAGE_SAGAMAAL'] = 'LANGUAGE_SAGAMAAL'
    level: Level = _level()

    @classmethod
    def name(cls) -> str:
        return 'Language Sagamål'


class LanguageDarrian(Skill):
    kind: Literal['LANGUAGE_DARRIAN'] = 'LANGUAGE_DARRIAN'
    level: Level = _level()

    @classmethod
    def name(cls) -> str:
        return 'Language Te-Zlodh'


class Leadership(Skill):
    kind: Literal['LEADERSHIP'] = 'LEADERSHIP'
    level: Level = _level()


class Mechanic(Skill):
    kind: Literal['MECHANIC'] = 'MECHANIC'
    level: Level = _level()


class Medic(Skill):
    kind: Literal['MEDIC'] = 'MEDIC'
    level: Level = _level()


class Melee(Skill):
    kind: Literal['MELEE'] = 'MELEE'
    unarmed: Level = _level('Unarmed')
    blade: Level = _level('Blade')
    bludgeon: Level = _level('Bludgeon')
    natural: Level = _level('Natural')
    grapple: Level = _level('Grapple')
    striking: Level = _level('Striking')
    fencing: Level = _level('Fencing')


class Navigation(Skill):
    kind: Literal['NAVIGATION'] = 'NAVIGATION'
    level: Level = _level()


class Persuade(Skill):
    kind: Literal['PERSUADE'] = 'PERSUADE'
    level: Level = _level()


class Pilot(Skill):
    kind: Literal['PILOT'] = 'PILOT'
    small_craft: Level = _level('Small Craft')
    spacecraft: Level = _level('Spacecraft')
    capital_ships: Level = _level('Capital Ships')


class ColonistProfession(Skill):
    kind: Literal['COLONIST_PROFESSION'] = 'COLONIST_PROFESSION'
    farming: Level = _level('Farming')
    ranching: Level = _level('Ranching')


class FreeloaderProfession(Skill):
    kind: Literal['FREELOADER_PROFESSION'] = 'FREELOADER_PROFESSION'
    scrounging: Level = _level('Scrounging')
    security: Level = _level('Security')


class HostileEnvironmentProfession(Skill):
    kind: Literal['HOSTILE_ENVIRONMENT_PROFESSION'] = 'HOSTILE_ENVIRONMENT_PROFESSION'
    contaminant: Level = _level('Contaminant')
    low_g: Level = _level('Low-G')
    high_g: Level = _level('High-G')
    underwater: Level = _level('Underwater')


class SpacerProfession(Skill):
    kind: Literal['SPACER_PROFESSION'] = 'SPACER_PROFESSION'
    belter: Level = _level('Belter')
    crewmember: Level = _level('Crewmember')


class SportProfession(Skill):
    kind: Literal['SPORT_PROFESSION'] = 'SPORT_PROFESSION'
    atmosphere_surfing: Level = _level('Atmosphere Surfing')
    golf: Level = _level('Golf')
    motorsports: Level = _level('Motorsports')
    racquet_sports: Level = _level('Racquet Sports')
    team_ball_sports: Level = _level('Team Ball Sports')
    track_and_field: Level = _level('Track & Field')


class WorkerProfession(Skill):
    kind: Literal['WORKER_PROFESSION'] = 'WORKER_PROFESSION'
    armourer: Level = _level('Armourer')
    biologicals: Level = _level('Biologicals')
    civil_engineering: Level = _level('Civil Engineering')
    construction: Level = _level('Construction')
    hydroponics: Level = _level('Hydroponics')
    metalworking: Level = _level('Metalworking')
    polymers: Level = _level('Polymers')


class Recon(Skill):
    kind: Literal['RECON'] = 'RECON'
    level: Level = _level()


class LifeScience(Skill):
    kind: Literal['LIFE_SCIENCE'] = 'LIFE_SCIENCE'
    biology: Level = _level('Biology')
    genetics: Level = _level('Genetics')
    psionicology: Level = _level('Psionicology')
    xenology: Level = _level('Xenology')


class PhysicalScience(Skill):
    kind: Literal['PHYSICAL_SCIENCE'] = 'PHYSICAL_SCIENCE'
    chemistry: Level = _level('Chemistry')
    physics: Level = _level('Physics')
    jumpspace_physics: Level = _level('Jumpspace Physics')


class RoboticScience(Skill):
    kind: Literal['ROBOTIC_SCIENCE'] = 'ROBOTIC_SCIENCE'
    cybernetics: Level = _level('Cybernetics')
    robotics: Level = _level('Robotics')


class SocialScience(Skill):
    kind: Literal['SOCIAL_SCIENCE'] = 'SOCIAL_SCIENCE'
    archaeology: Level = _level('Archaeology')
    economics: Level = _level('Economics')
    history: Level = _level('History')
    linguistics: Level = _level('Linguistics')
    philosophy: Level = _level('Philosophy')
    psychology: Level = _level('Psychology')
    sophontology: Level = _level('Sophontology')


class SpaceScience(Skill):
    kind: Literal['SPACE_SCIENCE'] = 'SPACE_SCIENCE'
    astronomy: Level = _level('Astronomy')
    cosmology: Level = _level('Cosmology')
    planetology: Level = _level('Planetology')


class Seafarer(Skill):
    kind: Literal['SEAFARER'] = 'SEAFARER'
    ocean_ships: Level = _level('Ocean Ships')
    personal: Level = _level('Personal')
    sail: Level = _level('Sail')
    submarine: Level = _level('Submarine')


class Stealth(Skill):
    kind: Literal['STEALTH'] = 'STEALTH'
    level: Level = _level()


class Steward(Skill):
    kind: Literal['STEWARD'] = 'STEWARD'
    level: Level = _level()


class Streetwise(Skill):
    kind: Literal['STREETWISE'] = 'STREETWISE'
    level: Level = _level()


class Survival(Skill):
    kind: Literal['SURVIVAL'] = 'SURVIVAL'
    level: Level = _level()


class Tactics(Skill):
    kind: Literal['TACTICS'] = 'TACTICS'
    military: Level = _level('Military')
    naval: Level = _level('Naval')


class VaccSuit(Skill):
    kind: Literal['VACC_SUIT'] = 'VACC_SUIT'
    level: Level = _level()


# Please Claude, don't be a fool and try to make this a type. It's not a type.
Arts = PerformingArt | CreativeArt | PresentationArt
type ArtSkill = Annotated[Arts, Field(discriminator='kind')]

# Please Claude, don't be a fool and try to make this a type. It's not a type.
Professions = (
    ColonistProfession
    | FreeloaderProfession
    | HostileEnvironmentProfession
    | SpacerProfession
    | SportProfession
    | WorkerProfession
)
type ProfessionSkill = Annotated[Professions, Field(discriminator='kind')]

# Please Claude, don't be a fool and try to make this a type. It's not a type.
Sciences = LifeScience | PhysicalScience | RoboticScience | SocialScience | SpaceScience
type ScienceSkill = Annotated[Sciences, Field(discriminator='kind')]

# Please Claude, don't be a fool and try to make this a type. It's not a type.
Languages = (
    LanguageGalanglic
    | LanguageVilani
    | LanguageZdetl
    | LanguageOynprith
    | LanguageTrokh
    | LanguageGvegh
    | LanguageAekhu
    | LanguageArrghoun
    | LanguageIrilitok
    | LanguageLogaksu
    | LanguageOvaghoun
    | LanguageSuedzuk
    | LanguageVuakedh
    | LanguageSagamaal
    | LanguageDarrian
)
type LanguageSkill = Annotated[Languages, Field(discriminator='kind')]

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
type BackgroundSkill = Annotated[BackgroundSkills, Field(discriminator='kind')]

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
    Field(discriminator='kind'),
]


def _skill_classes(skill_union: object) -> tuple[type[Skill], ...]:
    if hasattr(skill_union, '__value__'):
        skill_union = skill_union.__value__
    if get_origin(skill_union) is Annotated:
        skill_union = get_args(skill_union)[0]
    return get_args(skill_union)


def skill_instances(skill_union: object) -> list[AnySkill]:
    return [cast(AnySkill, cls()) for cls in _skill_classes(skill_union)]


def level_fields(skill_cls: type[Skill]) -> list[str]:
    return [
        name
        for name, field in skill_cls.model_fields.items()
        if name not in {'type', 'display_label'} and field.annotation is Level
    ]


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

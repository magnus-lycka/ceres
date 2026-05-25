from typing import Annotated, Any, Literal, cast, overload

from pydantic import BaseModel, Field

from ceres.character.benefits import AnyBenefit, ItemBenefit
from ceres.character.characteristics import Chars
from ceres.character.skills import AnySkill, Level, Skill
from ceres.shared import CeresModel


class PendingInputBase(BaseModel):
    id: str
    kind: str
    instruction: str
    options: list[str] = Field(default_factory=list)
    blocking: bool = True


class PendingUcp(PendingInputBase):
    kind: Literal['ucp'] = 'ucp'


class PendingBackgroundSkills(PendingInputBase):
    kind: Literal['background_skills'] = 'background_skills'


class PendingCareerChoice(PendingInputBase):
    kind: Literal['career_choice'] = 'career_choice'


class PendingSurvive(PendingInputBase):
    kind: Literal['survive'] = 'survive'


class PendingTermEvent(PendingInputBase):
    kind: Literal['term_event'] = 'term_event'


class PendingMishap(PendingInputBase):
    kind: Literal['mishap'] = 'mishap'


class PendingAdvancement(PendingInputBase):
    kind: Literal['advancement'] = 'advancement'


class PendingSkillTable(PendingInputBase):
    kind: Literal['skill_table'] = 'skill_table'


class PendingReenlist(PendingInputBase):
    kind: Literal['reenlist'] = 'reenlist'


class PendingMusterOut(PendingInputBase):
    kind: Literal['muster_out'] = 'muster_out'


class PendingSkillChoice(PendingInputBase):
    kind: Literal['skill_choice'] = 'skill_choice'


class PendingInitialTrainingChoice(PendingInputBase):
    kind: Literal['initial_training_choice'] = 'initial_training_choice'


class PendingSkillTableChoice(PendingInputBase):
    kind: Literal['skill_table_choice'] = 'skill_table_choice'


class PendingRankBonusChoice(PendingInputBase):
    kind: Literal['rank_bonus_choice'] = 'rank_bonus_choice'
    level: int


class PendingCharacteristicChoice(PendingInputBase):
    kind: Literal['characteristic_choice'] = 'characteristic_choice'


class PendingNearlyKilled(PendingInputBase):
    kind: Literal['nearly_killed'] = 'nearly_killed'


class PendingInjuryTable(PendingInputBase):
    kind: Literal['injury_table'] = 'injury_table'


class PendingDoubleInjuryRoll(PendingInputBase):
    """Roll 1D twice; system takes the lower result and applies Injury table."""

    kind: Literal['double_injury_roll'] = 'double_injury_roll'


class PendingBenefitChoice(PendingInputBase):
    """Player must pick one option from a ChoiceBenefit muster-out row."""

    kind: Literal['benefit_choice_pending'] = 'benefit_choice_pending'
    benefit_options: list[AnyBenefit]


class PendingAgingRoll(PendingInputBase):
    kind: Literal['aging_roll'] = 'aging_roll'


class PendingAgingChoice(PendingInputBase):
    kind: Literal['aging_choice'] = 'aging_choice'


class PendingAgingChoiceMental(PendingInputBase):
    kind: Literal['aging_choice_mental'] = 'aging_choice_mental'


class PendingAgingCrisis(PendingInputBase):
    kind: Literal['aging_crisis'] = 'aging_crisis'


class PendingLifeEvent(PendingInputBase):
    kind: Literal['life_event'] = 'life_event'


class PendingLifeEventChoice(PendingInputBase):
    """Life event that requires a connection kind choice (rolls 4 and 8)."""

    kind: Literal['life_event_choice'] = 'life_event_choice'
    roll: int


class PendingLifeEventUnusual(PendingInputBase):
    kind: Literal['life_event_unusual'] = 'life_event_unusual'


class PendingConnectionsRoll(PendingInputBase):
    kind: Literal['connections_roll'] = 'connections_roll'


class PendingCareerEvent(PendingInputBase):
    """Career-specific event requiring player input; career+roll identifies the exact event."""

    kind: Literal['career_event'] = 'career_event'
    career: str
    roll: int


class PendingCareerMishap(PendingInputBase):
    """Career-specific mishap requiring player input; career+roll identifies the exact mishap."""

    kind: Literal['career_mishap'] = 'career_mishap'
    career: str
    roll: int


class PendingCareerSkillChoice(PendingInputBase):
    """Skill choice triggered by a career event or mishap."""

    kind: Literal['career_skill_choice'] = 'career_skill_choice'
    career: str
    roll: int
    mishap: bool = False
    advancement_precreated: bool = False


class PendingCareerSkillRoll(PendingInputBase):
    """Skill roll required by a specific career event; context matches SkillRollEvent.context."""

    kind: Literal['career_skill_roll'] = 'career_skill_roll'
    career: str
    roll: int
    context: str


type AnyPending = Annotated[
    PendingUcp
    | PendingBackgroundSkills
    | PendingCareerChoice
    | PendingSurvive
    | PendingTermEvent
    | PendingMishap
    | PendingAdvancement
    | PendingSkillTable
    | PendingReenlist
    | PendingMusterOut
    | PendingSkillChoice
    | PendingInitialTrainingChoice
    | PendingSkillTableChoice
    | PendingRankBonusChoice
    | PendingCharacteristicChoice
    | PendingNearlyKilled
    | PendingInjuryTable
    | PendingDoubleInjuryRoll
    | PendingBenefitChoice
    | PendingAgingRoll
    | PendingAgingChoice
    | PendingAgingChoiceMental
    | PendingAgingCrisis
    | PendingLifeEvent
    | PendingLifeEventChoice
    | PendingLifeEventUnusual
    | PendingConnectionsRoll
    | PendingCareerEvent
    | PendingCareerMishap
    | PendingCareerSkillChoice
    | PendingCareerSkillRoll,
    Field(discriminator='kind'),
]


class ScheduledEffect(BaseModel):
    trigger: str
    source_event_id: int
    effect: dict = Field(default_factory=dict)
    expires: str | None = None
    consume: bool = True


class Connection(CeresModel):
    """Base class for character connections (contacts, allies, rivals, enemies)."""

    source: str = ''  # how/when this person entered the character's life
    power: int | None = None  # 1-6: degree of power or influence
    affinity: int | None = None  # 1-6: degree of affinity towards the Traveller
    enmity: int | None = None  # 1-6: degree of enmity towards the Traveller


class Contact(Connection):
    kind: Literal['contact'] = 'contact'


class Ally(Connection):
    kind: Literal['ally'] = 'ally'


class Rival(Connection):
    kind: Literal['rival'] = 'rival'


class Enemy(Connection):
    kind: Literal['enemy'] = 'enemy'


type AnyConnection = Annotated[
    Contact | Ally | Rival | Enemy,
    Field(discriminator='kind'),
]


def make_connection(
    kind: Literal['contact', 'ally', 'rival', 'enemy'],
    source: str = '',
    power: int | None = None,
) -> AnyConnection:
    match kind:
        case 'contact':
            return Contact(source=source, power=power)
        case 'ally':
            return Ally(source=source, power=power)
        case 'rival':
            return Rival(source=source, power=power)
        case 'enemy':
            return Enemy(source=source, power=power)


class CharacterSummary(BaseModel):
    name: str | None = None
    age: int = 18
    species: str | None = None
    characteristics: dict[Chars, int] = Field(default_factory=dict)
    current_career: str | None = None
    current_assignment: str | None = None
    last_career: str | None = None  # career name after muster-out
    last_assignment: str | None = None  # assignment name after muster-out
    rank: int | None = None
    term_count: int = 0
    skills: list[AnySkill] = Field(default_factory=list)
    connections: list[AnyConnection] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    narrative: list[str] = Field(default_factory=list)
    cash: int = 0
    benefits: list[ItemBenefit] = Field(default_factory=list)
    muster_out_cash_count: int = 0
    dead: bool = False

    @overload
    def skill_level(self, name: str, default: int) -> int: ...
    @overload
    def skill_level(self, name: str, default: None = None) -> int | None: ...
    def skill_level(self, name: str, default: int | None = None) -> int | None:
        for skill in self.skills:
            if type(skill).name() == name:
                fields = _level_fields(type(skill))
                if not fields:
                    return 0
                return max(getattr(skill, f).value for f in fields)
        return default


def _level_fields(skill_cls: type[Skill]) -> list[str]:
    return [
        name
        for name, field in skill_cls.model_fields.items()
        if name not in {'type', 'display_label'} and field.annotation is Level
    ]


class CharacterProjection(BaseModel):
    character_id: int
    summary: CharacterSummary = Field(default_factory=CharacterSummary)
    pending_inputs: list[AnyPending] = Field(default_factory=list)
    scheduled_effects: list[ScheduledEffect] = Field(default_factory=list)
    pending_reenlist: bool | None = None  # stores reenlist decision during aging chain
    muster_out_career: str | None = None  # career name used to look up benefit table

    def skill_choices(
        self,
        skill_types: list[type[Skill]],
        level: int | None,
    ) -> list[AnySkill]:
        choices: list[AnySkill] = []
        for skill_cls in skill_types:
            existing = next((s for s in self.summary.skills if type(s) is skill_cls), None)
            fields = _level_fields(skill_cls)
            _cls: Any = skill_cls
            if len(fields) == 1 and fields[0] == 'level':
                # Non-specialised skill
                current = getattr(existing, 'level').value if existing is not None else None
                if level is None:
                    if current is None or current < 4:
                        new_level = 1 if current is None else current + 1
                        choices.append(cast(AnySkill, _cls(level=Level(value=new_level))))
                else:
                    actual = current if current is not None else -1
                    if actual < level:
                        choices.append(cast(AnySkill, _cls(level=Level(value=level))))
            else:
                # Specialised skill
                if level == 0:
                    # Level-0 grant adds the whole type if absent
                    if existing is None:
                        choices.append(cast(AnySkill, _cls()))
                elif level is None:
                    # Increment — one choice per specialization field
                    for field in fields:
                        current = getattr(existing, field).value if existing is not None else 0
                        if current < 4:
                            choices.append(cast(AnySkill, _cls(**{field: Level(value=current + 1)})))
                else:
                    # Fixed level > 0 — one choice per spec currently below target
                    for field in fields:
                        current = getattr(existing, field).value if existing is not None else 0
                        if current < level:
                            choices.append(cast(AnySkill, _cls(**{field: Level(value=level)})))
        return choices

    def check_skill_choice(
        self,
        skill_types: list[type[Skill]],
        level: int | None,
        choice: AnySkill,
    ) -> bool:
        return choice in self.skill_choices(skill_types, level)


__all__ = [
    'Ally',
    'AnyConnection',
    'AnyPending',
    'CharacterProjection',
    'CharacterSummary',
    'Connection',
    'Contact',
    'Enemy',
    'make_connection',
    'PendingAdvancement',
    'Rival',
    'PendingAgingChoice',
    'PendingAgingChoiceMental',
    'PendingAgingCrisis',
    'PendingAgingRoll',
    'PendingBackgroundSkills',
    'PendingBenefitChoice',
    'PendingCareerChoice',
    'PendingCareerEvent',
    'PendingCareerMishap',
    'PendingCareerSkillChoice',
    'PendingCareerSkillRoll',
    'PendingCharacteristicChoice',
    'PendingConnectionsRoll',
    'PendingDoubleInjuryRoll',
    'PendingInitialTrainingChoice',
    'PendingInputBase',
    'PendingInjuryTable',
    'PendingLifeEvent',
    'PendingLifeEventChoice',
    'PendingLifeEventUnusual',
    'PendingMishap',
    'PendingMusterOut',
    'PendingNearlyKilled',
    'PendingRankBonusChoice',
    'PendingReenlist',
    'PendingSkillChoice',
    'PendingSkillTable',
    'PendingSkillTableChoice',
    'PendingSurvive',
    'PendingTermEvent',
    'PendingUcp',
    'ScheduledEffect',
]

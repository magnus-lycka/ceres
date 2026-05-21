from typing import Annotated, Literal

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    id: int = 0  # assigned by store; 0 means unassigned
    fulfills: str | None = None


class CharacterStartedEvent(EventBase):
    kind: Literal['character_started'] = 'character_started'
    sophont: str
    player: str = 'NPC'
    name: str


class UcpEvent(EventBase):
    kind: Literal['ucp'] = 'ucp'
    ucp: str


class BackgroundSkillsEvent(EventBase):
    kind: Literal['background_skills'] = 'background_skills'
    skills: list[str]


class CareerEvent(EventBase):
    kind: Literal['career'] = 'career'
    career: str
    assignment: str


class SurviveEvent(EventBase):
    kind: Literal['survive'] = 'survive'
    roll: int  # sum of 2D, before characteristic DM


class MishapEvent(EventBase):
    kind: Literal['mishap'] = 'mishap'
    roll: int  # 1D result
    stay_in_career: bool = False  # True when the event says "mishap but you are not ejected"


class TermEventEvent(EventBase):
    kind: Literal['term_event'] = 'term_event'
    roll: int  # sum of 2D


class SkillChoiceEvent(EventBase):
    kind: Literal['skill_choice'] = 'skill_choice'
    skill: str


class AdvancementEvent(EventBase):
    kind: Literal['advancement'] = 'advancement'
    roll: int  # sum of 2D, before characteristic DM


class ReenlistEvent(EventBase):
    kind: Literal['reenlist'] = 'reenlist'
    reenlist: bool


class SkillTableEvent(EventBase):
    kind: Literal['skill_table'] = 'skill_table'
    table: str  # 'personal_development', 'service_skills', 'advanced_education', or assignment name
    roll: int  # 1D result (1-6)


class CharacteristicChoiceEvent(EventBase):
    kind: Literal['characteristic_choice'] = 'characteristic_choice'
    characteristic: str  # the chosen characteristic to apply the pending effect to
    amount: int = 1  # how much to reduce the characteristic by


class ConnectionsRollEvent(EventBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: Literal['contact', 'ally', 'rival', 'enemy']
    count: int  # final count (client applies the dice expression from the pending instruction)


class SkillRollEvent(EventBase):
    kind: Literal['skill_roll'] = 'skill_roll'
    context: str  # matches the pending kind — dispatch key for the career handler
    skill: str  # which skill was chosen
    modified_roll: int  # 2D + skill level + any other DMs already applied by the player


type AnyEvent = Annotated[
    CharacterStartedEvent
    | UcpEvent
    | BackgroundSkillsEvent
    | CareerEvent
    | SurviveEvent
    | MishapEvent
    | TermEventEvent
    | SkillChoiceEvent
    | AdvancementEvent
    | ReenlistEvent
    | SkillTableEvent
    | CharacteristicChoiceEvent
    | ConnectionsRollEvent
    | SkillRollEvent,
    Field(discriminator='kind'),
]


__all__ = [
    'AnyEvent',
    'AdvancementEvent',
    'BackgroundSkillsEvent',
    'CareerEvent',
    'CharacteristicChoiceEvent',
    'CharacterStartedEvent',
    'ConnectionsRollEvent',
    'EventBase',
    'MishapEvent',
    'ReenlistEvent',
    'SkillChoiceEvent',
    'SkillRollEvent',
    'SkillTableEvent',
    'SurviveEvent',
    'TermEventEvent',
    'UcpEvent',
]

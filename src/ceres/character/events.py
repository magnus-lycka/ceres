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
    qualification_roll: int  # 2D result before characteristic DM


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


class AgingRollEvent(EventBase):
    kind: Literal['aging_roll'] = 'aging_roll'
    roll: int  # 2D result (2-12) before the -term_count DM


class InjuryTableEvent(EventBase):
    kind: Literal['injury_table'] = 'injury_table'
    roll: int  # 1D result (1-6) on the Injury table


class LifeEventEvent(EventBase):
    kind: Literal['life_event'] = 'life_event'
    roll: int  # 2D result (2-12) on the Life Events table


class LifeEventUnusualEvent(EventBase):
    kind: Literal['life_event_unusual'] = 'life_event_unusual'
    roll: int  # 1D result (1-6) on the Unusual Event sub-table


class MusterOutEvent(EventBase):
    kind: Literal['muster_out'] = 'muster_out'
    table: Literal['cash', 'benefits']
    roll: int  # 1D result (1-6), DMs already applied by player


type AnyEvent = Annotated[
    AgingRollEvent
    | CharacterStartedEvent
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
    | SkillRollEvent
    | InjuryTableEvent
    | LifeEventEvent
    | LifeEventUnusualEvent
    | MusterOutEvent,
    Field(discriminator='kind'),
]


__all__ = [
    'AnyEvent',
    'AdvancementEvent',
    'AgingRollEvent',
    'BackgroundSkillsEvent',
    'CareerEvent',
    'CharacteristicChoiceEvent',
    'CharacterStartedEvent',
    'ConnectionsRollEvent',
    'EventBase',
    'InjuryTableEvent',
    'LifeEventEvent',
    'LifeEventUnusualEvent',
    'MishapEvent',
    'MusterOutEvent',
    'ReenlistEvent',
    'SkillChoiceEvent',
    'SkillRollEvent',
    'SkillTableEvent',
    'SurviveEvent',
    'TermEventEvent',
    'UcpEvent',
]

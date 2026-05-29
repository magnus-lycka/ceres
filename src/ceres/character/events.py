from typing import Annotated, Literal

from pydantic import BaseModel, Field

from ceres.character.characteristics import Chars, ConnectionKind
from ceres.character.skills import AnySkill


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
    skills: list[AnySkill]


class CareerEvent(EventBase):
    kind: Literal['career'] = 'career'
    career: str
    assignment: str
    qualification_roll: int  # 2D result before characteristic DM


class DraftEvent(EventBase):
    kind: Literal['draft'] = 'draft'
    career: str
    assignment: str | None = None


class DraftAssignmentEvent(EventBase):
    kind: Literal['draft_assignment'] = 'draft_assignment'
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
    skill: AnySkill


class AdvancementDmChoiceEvent(EventBase):
    kind: Literal['advancement_dm_choice'] = 'advancement_dm_choice'


class ConnectionKindChoiceEvent(EventBase):
    kind: Literal['connection_kind_choice'] = 'connection_kind_choice'
    connection_kind: ConnectionKind


class CareerChoiceEvent(EventBase):
    """Generic career-specific choice event replacing per-career event types."""

    kind: Literal['career_decision'] = 'career_decision'
    context: str  # key into the career's CHOICE_HANDLERS registry
    choice: str


class AdvancementEvent(EventBase):
    kind: Literal['advancement'] = 'advancement'
    roll: int  # sum of 2D, before characteristic DM


class CommissionEvent(EventBase):
    kind: Literal['commission'] = 'commission'
    attempt: bool
    roll: int = 0  # sum of 2D, before characteristic DM and term DM; ignored when attempt is False


class ReenlistEvent(EventBase):
    kind: Literal['reenlist'] = 'reenlist'
    reenlist: bool


class SkillTableEvent(EventBase):
    kind: Literal['skill_table'] = 'skill_table'
    table: str  # 'personal_development', 'service_skills', 'advanced_education', or assignment name
    roll: int  # 1D result (1-6)


class CharacteristicChoiceEvent(EventBase):
    kind: Literal['characteristic_choice'] = 'characteristic_choice'
    characteristic: Chars  # the chosen characteristic to apply the pending effect to
    amount: int = 1  # how much to reduce the characteristic by


class ConnectionsRollEvent(EventBase):
    kind: Literal['connections_roll'] = 'connections_roll'
    connection_type: ConnectionKind
    count: int  # final count (client applies the dice expression from the pending instruction)


class SkillRollEvent(EventBase):
    kind: Literal['skill_roll'] = 'skill_roll'
    context: str  # matches the pending kind — dispatch key for the career handler
    skill: AnySkill | Chars  # Chars for characteristic rolls (EDU, INT, etc.)
    modified_roll: int  # 2D + skill level + any other DMs already applied by the player


class AgingRollEvent(EventBase):
    kind: Literal['aging_roll'] = 'aging_roll'
    roll: int  # 2D result (2-12) before the -term_count DM


class InjuryTableEvent(EventBase):
    kind: Literal['injury_table'] = 'injury_table'
    roll: int  # 1D result (1-6) on the Injury table


class DoubleInjuryTableEvent(EventBase):
    """Roll twice on the Injury table; the system takes the lower result."""

    kind: Literal['double_injury_table'] = 'double_injury_table'
    roll1: int  # first 1D result (1-6)
    roll2: int  # second 1D result (1-6)


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


class BenefitChoiceEvent(EventBase):
    """Resolves a PendingBenefitChoice by selecting one option from the list."""

    kind: Literal['benefit_choice'] = 'benefit_choice'
    choice_index: int  # 0-based index into PendingBenefitChoice.benefit_options


class AgingCrisisEvent(EventBase):
    kind: Literal['aging_crisis'] = 'aging_crisis'
    paid: bool
    medical_roll: int = 0  # 1D result for medical cost; 0 if not paying


class AssignmentChangeChoiceEvent(EventBase):
    """End-of-term choice for careers that allow intra-career assignment changes.

    choice is one of: 'same' (reenlist same assignment), 'muster_out', or an assignment name
    to attempt. When an assignment name is given, qualification_roll must be provided; on
    failure a PendingReenlist is created for the character to choose same or muster out.
    """

    kind: Literal['assignment_change_choice'] = 'assignment_change_choice'
    choice: str  # 'same', 'muster_out', or target assignment name
    qualification_roll: int | None = None  # required when choice is an assignment name


class FinishCreationEvent(EventBase):
    """Player chooses to end character creation after completing muster out."""

    kind: Literal['finish_creation'] = 'finish_creation'


class PreCareerEntryEvent(EventBase):
    """Attempt to enter pre-career education (university or military academy)."""

    kind: Literal['precareer_entry'] = 'precareer_entry'
    precareer: str
    roll: int  # 2D result for entry check (before characteristic DM)


class PreCareerSkillChoiceEvent(EventBase):
    """Choose a skill gained during university pre-career; level is set by the pending input."""

    kind: Literal['precareer_skill_choice'] = 'precareer_skill_choice'
    skill: str  # specific skill name (may include specialisation, e.g. 'Science (biology)')


class PreCareerEventEvent(EventBase):
    """Roll on the Pre-career Events table."""

    kind: Literal['precareer_event'] = 'precareer_event'
    roll: int  # 2D result (2-12)


class PreCareerGraduationEvent(EventBase):
    """Roll for graduation from pre-career education."""

    kind: Literal['precareer_graduation'] = 'precareer_graduation'
    roll: int  # 2D result for graduation check (before characteristic DM)


type AnyEvent = Annotated[
    AgingCrisisEvent
    | AgingRollEvent
    | AdvancementDmChoiceEvent
    | CharacterStartedEvent
    | UcpEvent
    | BackgroundSkillsEvent
    | CareerEvent
    | DraftEvent
    | DraftAssignmentEvent
    | SurviveEvent
    | MishapEvent
    | TermEventEvent
    | SkillChoiceEvent
    | AdvancementEvent
    | CommissionEvent
    | ReenlistEvent
    | SkillTableEvent
    | CharacteristicChoiceEvent
    | ConnectionsRollEvent
    | ConnectionKindChoiceEvent
    | SkillRollEvent
    | InjuryTableEvent
    | DoubleInjuryTableEvent
    | LifeEventEvent
    | LifeEventUnusualEvent
    | MusterOutEvent
    | BenefitChoiceEvent
    | CareerChoiceEvent
    | AssignmentChangeChoiceEvent
    | FinishCreationEvent
    | PreCareerEntryEvent
    | PreCareerSkillChoiceEvent
    | PreCareerEventEvent
    | PreCareerGraduationEvent,
    Field(discriminator='kind'),
]


__all__ = [
    'AnyEvent',
    'AdvancementDmChoiceEvent',
    'ConnectionKind',
    'AdvancementEvent',
    'AgingCrisisEvent',
    'AgingRollEvent',
    'AssignmentChangeChoiceEvent',
    'BackgroundSkillsEvent',
    'BenefitChoiceEvent',
    'CareerChoiceEvent',
    'CareerEvent',
    'CharacteristicChoiceEvent',
    'CharacterStartedEvent',
    'CommissionEvent',
    'ConnectionKindChoiceEvent',
    'ConnectionsRollEvent',
    'DraftEvent',
    'DraftAssignmentEvent',
    'FinishCreationEvent',
    'PreCareerEntryEvent',
    'PreCareerSkillChoiceEvent',
    'PreCareerEventEvent',
    'PreCareerGraduationEvent',
    'DoubleInjuryTableEvent',
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

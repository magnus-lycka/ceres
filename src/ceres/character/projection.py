from typing import Literal

from pydantic import BaseModel, Field


class PendingInput(BaseModel):
    id: str
    kind: str
    instruction: str
    options: list[str] = Field(default_factory=list)
    blocking: bool = True


class ScheduledEffect(BaseModel):
    trigger: str
    source_event_id: int
    effect: dict = Field(default_factory=dict)
    expires: str | None = None
    consume: bool = True


class Connection(BaseModel):
    kind: Literal['contact', 'ally', 'rival', 'enemy']
    source: str = ''  # how/when this person entered the character's life


class CharacterSummary(BaseModel):
    name: str | None = None
    age: int = 18
    species: str | None = None
    characteristics: dict[str, int] = Field(default_factory=dict)
    current_career: str | None = None
    current_assignment: str | None = None
    rank: int | None = None
    term_count: int = 0
    skills: dict[str, int] = Field(default_factory=dict)
    connections: list[Connection] = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)
    cash: int = 0
    benefits: list[str] = Field(default_factory=list)
    muster_out_cash_count: int = 0
    dead: bool = False


class CharacterProjection(BaseModel):
    character_id: int
    summary: CharacterSummary = Field(default_factory=CharacterSummary)
    pending_inputs: list[PendingInput] = Field(default_factory=list)
    scheduled_effects: list[ScheduledEffect] = Field(default_factory=list)
    pending_reenlist: bool | None = None  # stores reenlist decision during aging chain
    muster_out_career: str | None = None  # career name used to look up benefit table


__all__ = [
    CharacterProjection,
    CharacterSummary,
    Connection,
    PendingInput,
    ScheduledEffect,
]

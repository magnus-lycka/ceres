from pydantic import BaseModel, Field


class PendingInput(BaseModel):
    id: str
    kind: str
    instruction: str
    blocking: bool = True


class ScheduledEffect(BaseModel):
    trigger: str
    source_event_id: int
    effect: dict = Field(default_factory=dict)
    expires: str | None = None
    consume: bool = True


class CharacterSummary(BaseModel):
    name: str | None = None
    age: int = 18
    species: str | None = None
    characteristics: dict[str, int] = Field(default_factory=dict)
    current_career: str | None = None
    current_assignment: str | None = None
    rank: str | int | None = None
    term_count: int = 0
    skills: list = Field(default_factory=list)
    problems: list[str] = Field(default_factory=list)


class CharacterProjection(BaseModel):
    character_id: int
    summary: CharacterSummary = Field(default_factory=CharacterSummary)
    pending_inputs: list[PendingInput] = Field(default_factory=list)
    scheduled_effects: list[ScheduledEffect] = Field(default_factory=list)


__all__ = [
    'CharacterProjection',
    'CharacterSummary',
    'PendingInput',
    'ScheduledEffect',
]

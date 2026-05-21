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


type AnyEvent = Annotated[
    CharacterStartedEvent | UcpEvent,
    Field(discriminator='kind'),
]


__all__ = [
    'AnyEvent',
    'CharacterStartedEvent',
    'EventBase',
    'UcpEvent',
]

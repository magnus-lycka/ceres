"""What is stored: an Actor, a Party of them, and a Situation they fight in.

These are documents, not the live fight. They carry no rounds, no turn state
and no damage — that belongs to `ceres.rounds.domain`, which is handed these to
work from.
"""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator

from ceres.rounds.library.ids import UNSAVED, ActorId, PartyId, SituationId


class ActorKind(StrEnum):
    """What kind of body an actor has, which decides how it absorbs damage."""

    SOPHONT = 'sophont'
    ANIMAL = 'animal'
    ROBOT = 'robot'


CHARACTERISTICS = ('strength', 'dexterity', 'endurance')


class Actor(BaseModel):
    """One individual. Five identical guards are five Actors, not one with a count."""

    id: ActorId = ActorId(UNSAVED)
    name: str
    kind: ActorKind
    note: str = ''
    tags: list[str] = Field(default_factory=list)

    strength: int | None = None
    dexterity: int | None = None
    endurance: int | None = None
    hits: int | None = None

    @model_validator(mode='after')
    def _check_kind_has_what_it_needs(self) -> Self:
        """A sophont is hurt through STR/DEX/END; anything else through Hits."""
        wants_characteristics = self.kind is ActorKind.SOPHONT
        missing = [name for name in CHARACTERISTICS if getattr(self, name) is None]
        if wants_characteristics and missing:
            msg = f'a {self.kind} needs {", ".join(missing)}'
            raise ValueError(msg)
        if not wants_characteristics and len(missing) < len(CHARACTERISTICS):
            msg = f'a {self.kind} has no characteristics, only Hits'
            raise ValueError(msg)
        if not wants_characteristics and self.hits is None:
            msg = f'a {self.kind} needs hits'
            raise ValueError(msg)
        return self


class Party(BaseModel):
    """A reusable named set of actors: the PCs, a wolf pack, starport security.

    Holds no initiative and no combat state. A Situation copies a Party rather
    than pointing at it, so this may be edited or deleted freely afterwards.
    """

    id: PartyId = PartyId(UNSAVED)
    name: str
    note: str = ''
    tags: list[str] = Field(default_factory=list)
    actors: list[ActorId] = Field(default_factory=list)

    @property
    def size(self) -> int:
        """Members as stored, including any whose Actor has since been deleted."""
        return len(self.actors)


class Member(BaseModel):
    """One actor's place in one Situation: a reference plus local facts.

    `party` is a plain copied name, not a reference, so it survives the Party
    being renamed or deleted. Everything else here belongs to the fight and
    means nothing outside it.
    """

    actor: ActorId
    party: str = ''
    initiative: int | None = None


class Situation(BaseModel):
    """A fight. Usually made on the spot and thrown away soon after.

    Preparing one has to be quick, because most of them cannot be prepared at
    all: the referee finds out a fight is happening at the same time as the
    players do.
    """

    id: SituationId = SituationId(UNSAVED)
    name: str
    note: str = ''
    members: list[Member] = Field(default_factory=list)

    def member_for(self, actor: ActorId, *, party: str = '') -> Member:
        return Member(actor=actor, party=party)

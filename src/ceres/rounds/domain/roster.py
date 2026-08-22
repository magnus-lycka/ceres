"""Actors and parties available to round-by-round situations."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ceres.rounds.domain.actor import Actor


class Party:
    """A reusable side whose members may share an initiative value."""

    def __init__(self, name: str, initiative: int | None = None):
        self.name = name
        self.initiative = initiative

    def __repr__(self) -> str:
        return f'Party({self.name!r})'


class Roster:
    """Reusable parties and actors, whether or not they are currently active."""

    def __init__(self) -> None:
        self.parties: list[Party] = []
        self.actors: list[Actor] = []

    def add_party(self, name: str, initiative: int | None = None) -> Party:
        party = Party(name, initiative)
        self.parties.append(party)
        return party

    def add_actor(self, actor: Actor) -> Actor:
        if actor.party not in self.parties:
            msg = 'actor party must belong to this roster'
            raise ValueError(msg)
        if actor not in self.actors:
            self.actors.append(actor)
        return actor

    def remove_actor(self, actor: Actor) -> None:
        self.actors.remove(actor)

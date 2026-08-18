"""A situation run round by round: a fight, a fire, a hull breach.

Owns the roster, the parties, the round counter and the initiative step that
decides who is currently green.
"""

from ceres.rounds.domain.actor import Actor, TurnState

ROUND_SECONDS = 6


class Party:
    """A side. May hold one shared initiative for all its members (:36)."""

    def __init__(self, name: str, initiative: int | None = None):
        self.name = name
        self.initiative = initiative

    def __repr__(self) -> str:
        return f'Party({self.name!r})'


class Situation:
    def __init__(self, name: str = ''):
        self.name = name
        self.parties: list[Party] = []
        self.actors: list[Actor] = []
        self.round_number = 0
        self._step: int | None = None

    @property
    def elapsed_seconds(self) -> int:
        """Each combat round lasts around six seconds of game time (:60)."""
        return self.round_number * ROUND_SECONDS

    def add_party(self, name: str, initiative: int | None = None) -> Party:
        party = Party(name, initiative)
        self.parties.append(party)
        return party

    def set_party_initiative(self, party: Party, initiative: int) -> None:
        """One check for a whole side, in one operation."""
        party.initiative = initiative

    def add_actor(self, actor: Actor) -> Actor:
        self.actors.append(actor)
        if self._step is not None and actor.initiative_value >= self._step:
            actor.make_ready()
        return actor

    def withdraw(self, actor: Actor) -> None:
        self.actors.remove(actor)

    def turn_order(self) -> list[Actor]:
        """Highest initiative first, ties broken by DEX (:62)."""
        return sorted(self.actors, key=lambda a: (-a.initiative_value, -a.dexterity, a.name))

    def new_round(self) -> None:
        self.round_number += 1
        for actor in self.actors:
            actor.begin_round()
        self._step = None
        self._open_highest_step()

    def act(self, actor: Actor) -> None:
        actor.act()
        self._advance_step_if_ready()

    def wait(self, actor: Actor) -> None:
        actor.wait()
        self._advance_step_if_ready()

    def _open_highest_step(self) -> None:
        values = self._initiative_values()
        if values:
            self._step = values[0]
            self._make_ready_at_step()

    def _initiative_values(self) -> list[int]:
        return sorted({a.initiative_value for a in self.actors}, reverse=True)

    def _make_ready_at_step(self) -> None:
        for actor in self.actors:
            if actor.initiative_value == self._step:
                actor.make_ready()

    def _advance_step_if_ready(self) -> None:
        """Open the next initiative step once the current one has been offered.

        Actors who waited stay green and may still act, so the trigger is that
        everyone at this step has either acted or explicitly waited.
        """
        while self._step is not None and self._step_is_settled():
            lower = [v for v in self._initiative_values() if v < self._step]
            if not lower:
                self._step = None
                return
            self._step = lower[0]
            self._make_ready_at_step()

    def _step_is_settled(self) -> bool:
        at_step = [a for a in self.actors if a.initiative_value == self._step]
        return all(a.has_had_their_turn or not a.can_act for a in at_step)

    @property
    def ready_actors(self) -> list[Actor]:
        return [a for a in self.turn_order() if a.turn_state is TurnState.READY]

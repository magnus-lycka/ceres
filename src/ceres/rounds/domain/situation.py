"""A situation run round by round: a fight, a fire, a hull breach.

Owns the roster, the parties, the round counter and the initiative step that
decides who is currently green.
"""

from ceres.rounds.domain.actions import AttackKind, ReactionKind
from ceres.rounds.domain.actor import Actor, ActorCondition, TurnState
from ceres.rounds.domain.damage import DamageKind
from ceres.rounds.domain.roster import Party, Roster

ROUND_SECONDS = 6


class Situation:
    def __init__(self, name: str = '', *, roster: Roster | None = None):
        self.name = name
        self.roster = roster or Roster()
        self.actors: list[Actor] = []
        self.round_number = 0
        self._step: int | None = None

    @property
    def parties(self) -> list[Party]:
        return self.roster.parties

    @property
    def elapsed_seconds(self) -> int:
        """Each combat round lasts around six seconds of game time (:60)."""
        return self.round_number * ROUND_SECONDS

    def add_party(self, name: str, initiative: int | None = None) -> Party:
        return self.roster.add_party(name, initiative)

    def set_party_initiative(self, party: Party, initiative: int) -> None:
        """One check for a whole side, in one operation."""
        party.initiative = initiative

    def add_actor(self, actor: Actor) -> Actor:
        """Register an actor and include them in this situation."""
        self.roster.add_actor(actor)
        self.include(actor)
        return actor

    def include(self, actor: Actor) -> None:
        """Include a roster actor in the active situation."""
        if actor not in self.roster.actors:
            msg = 'actor must belong to the situation roster'
            raise ValueError(msg)
        if actor in self.actors:
            return
        self.actors.append(actor)
        if self._step is not None and actor.initiative_value >= self._step:
            actor.make_ready()

    def withdraw(self, actor: Actor) -> None:
        """Remove an actor from this situation but retain them on the roster."""
        self.actors.remove(actor)
        self._advance_step_if_ready()

    def remove_from_roster(self, actor: Actor) -> None:
        """Remove an actor from both the situation and its reusable roster."""
        if actor in self.actors:
            self.withdraw(actor)
        self.roster.remove_actor(actor)

    def is_participating(self, actor: Actor) -> bool:
        return actor in self.actors

    def turn_order(self) -> list[Actor]:
        """Highest initiative first, ties broken by DEX (:62)."""
        return sorted(self.actors, key=lambda a: (-a.initiative_value, -a.dexterity, a.name))

    def new_round(self) -> None:
        self.round_number += 1
        for actor in self.actors:
            actor.begin_round()
        self._step = None
        self._open_highest_step()

    def finish_turn(self, actor: Actor) -> None:
        actor.finish_turn()
        self._advance_step_if_ready()

    def attack(
        self,
        attacker: Actor | None,
        target: Actor,
        kind: AttackKind | None = None,
        *,
        lethal: int = 0,
        stun: int = 0,
    ) -> None:
        """Apply net damage and finish an actor source's turn.

        ``None`` represents Other: falls, fire, vacuum, and similar injury do
        not consume the turn of any actor in the roster.
        """
        if attacker is None:
            if kind is not None:
                msg = 'Other has no attack kind'
                raise ValueError(msg)
            target.track.apply(lethal, DamageKind.LETHAL)
            target.track.apply(stun, DamageKind.STUN)
            return
        if kind is None:
            msg = 'an actor source needs Melee or Ranged'
            raise ValueError(msg)
        target.track.apply(lethal, DamageKind.LETHAL)
        target.track.apply(stun, DamageKind.STUN)
        attacker.last_action = f'{kind.value} {target.name}'
        self.finish_turn(attacker)

    def react(self, actor: Actor, reaction: ReactionKind) -> None:
        actor.react(reaction)
        if reaction is ReactionKind.DIVE:
            self._advance_step_if_ready()

    def wait(self, actor: Actor) -> None:
        actor.wait()
        self._advance_step_if_ready()

    def clear_condition(self, actor: Actor, condition: ActorCondition) -> None:
        actor.clear_condition(condition)

    def correct_actor(
        self,
        actor: Actor,
        *,
        name: str,
        party: Party,
        initiative: int | None,
        turn_state: TurnState,
        reaction_dm: int,
        last_action: str,
        conditions: set[ActorCondition],
        forfeit_next_turn: bool,
        waited: bool,
    ) -> None:
        """Correct an actor's editable facts without recording an action."""
        if not name.strip():
            msg = 'name cannot be empty'
            raise ValueError(msg)
        if party not in self.parties:
            msg = 'party must belong to this situation'
            raise ValueError(msg)
        actor.name = name.strip()
        actor.party = party
        actor.initiative = initiative
        actor.correct_round_state(
            turn_state=turn_state,
            reaction_dm=reaction_dm,
            last_action=last_action,
            conditions=conditions,
            forfeit_next_turn=forfeit_next_turn,
            waited=waited,
        )
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

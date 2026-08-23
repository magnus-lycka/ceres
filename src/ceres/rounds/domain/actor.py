"""Anyone taking turns: a PC, an NPC, an animal.

Called an actor rather than a combatant because a situation run in rounds need
not be a fight — it may be a fire, or a hull breach being patched against the
clock.
"""

from enum import StrEnum, auto
from typing import TYPE_CHECKING

from ceres.character.domain.characteristics import Chars
from ceres.rounds.domain.actions import ReactionKind
from ceres.rounds.domain.damage import DamageKind
from ceres.rounds.domain.tracks import CharacteristicTrack, DamageTrack

if TYPE_CHECKING:
    from ceres.rounds.domain.roster import Party


class TurnState(StrEnum):
    """Where an actor stands in the current round."""

    PENDING = auto()  # their initiative step has not been reached
    READY = auto()  # green: may act now, including after waiting
    ACTED = auto()  # grey: done until the next round


class ActorCondition(StrEnum):
    """Lasting, explicitly cleared combat conditions shown as UI tags."""

    PRONE = 'Prone'


class Actor:
    def __init__(
        self,
        *,
        name: str,
        party: Party,
        track: DamageTrack,
        initiative: int | None = None,
    ):
        self.name = name
        self.party = party
        self.track = track
        self.initiative = initiative
        self.turn_state = TurnState.PENDING
        self.waited = False
        self._round_started = False
        self._reaction_dm = 0
        self._next_reaction_dm = 0
        self._forfeit_next_turn = False
        self._conditions: set[ActorCondition] = set()
        self._incapacitated_until: int | None = None
        self.last_action = ''

    @property
    def initiative_value(self) -> int:
        """An individual initiative wins; otherwise the party's shared one (:36)."""
        if self.initiative is not None:
            return self.initiative
        return self.party.initiative or 0

    @property
    def dexterity(self) -> int:
        """Used only to break initiative ties (:62)."""
        if isinstance(self.track, CharacteristicTrack):
            return self.track.current(Chars.DEX)
        return 0

    @property
    def incapacitated_until(self) -> int | None:
        """The round stun wears off, counted by the situation this belongs to."""
        return self._incapacitated_until

    def take_damage(self, *, lethal: int = 0, stun: int = 0, at: int) -> None:
        """Absorb a hit in round `at` and note how long stun puts them out for."""
        self.track.apply(lethal, DamageKind.LETHAL, at=at)
        self._extend_incapacitation(self.track.apply(stun, DamageKind.STUN, at=at), at)

    def is_incapacitated(self, current_round: int) -> bool:
        """Put out of action by stun rather than by injury (:366)."""
        return self._incapacitated_until is not None and current_round < self._incapacitated_until

    def is_able_to_act(self, current_round: int) -> bool:
        """Whether injury or stun permits this actor to take a turn."""
        return not (self.track.is_dead or self.track.is_unconscious or self.is_incapacitated(current_round))

    def can_act(self, current_round: int) -> bool:
        return self.turn_state is TurnState.READY and self.is_able_to_act(current_round)

    def clear_stun(self) -> None:
        """The referee's stand-in for an hour of rest (:366)."""
        self.track.clear_stun()
        self._incapacitated_until = None

    def carry_over(self) -> None:
        """Their fight ended: the wounds stay, everything counted in it goes."""
        self.track.carry_over()
        self._incapacitated_until = None

    def _extend_incapacitation(self, rounds: int, at: int) -> None:
        """A later hit extends the wait; it never stacks on top of it."""
        if rounds > 0:
            self._incapacitated_until = max(self._incapacitated_until or 0, at + rounds)

    @property
    def reaction_dm(self) -> int:
        """Penalty on the next turn that has not already been finished."""
        if self._round_started and self.turn_state is not TurnState.ACTED:
            return self._reaction_dm
        return self._next_reaction_dm

    @property
    def conditions(self) -> frozenset[ActorCondition]:
        return frozenset(self._conditions)

    @property
    def forfeits_next_turn(self) -> bool:
        return self._forfeit_next_turn

    def begin_round(self) -> None:
        self._round_started = True
        self._reaction_dm = self._next_reaction_dm
        self._next_reaction_dm = 0
        if self._forfeit_next_turn:
            self.turn_state = TurnState.ACTED
            self._forfeit_next_turn = False
        else:
            self.turn_state = TurnState.PENDING
        self.waited = False

    def make_ready(self) -> None:
        if self.turn_state is TurnState.PENDING:
            self.turn_state = TurnState.READY
            self.waited = False

    def finish_turn(self) -> None:
        """Mark this actor done; the app does not inventory actions within a turn."""
        self.turn_state = TurnState.ACTED
        self.waited = False
        self._reaction_dm = 0

    def react(self, reaction: ReactionKind) -> None:
        """Attach a reaction to the next turn that has not been finished."""
        current_turn_is_unspent = self._round_started and self.turn_state is not TurnState.ACTED
        if reaction is ReactionKind.DIVE:
            self._conditions.add(ActorCondition.PRONE)
            if current_turn_is_unspent:
                self.finish_turn()
            else:
                self._forfeit_next_turn = True
            return
        if current_turn_is_unspent:
            self._reaction_dm -= 1
        else:
            self._next_reaction_dm -= 1

    def wait(self) -> None:
        """Delay the action until later in the turn (:32); stays green."""
        self.waited = True

    def clear_condition(self, condition: ActorCondition) -> None:
        """Clear a referee-managed condition without recording an action."""
        self._conditions.discard(condition)

    def correct_round_state(
        self,
        *,
        turn_state: TurnState,
        reaction_dm: int,
        last_action: str,
        conditions: set[ActorCondition],
        forfeit_next_turn: bool,
        waited: bool = False,
        incapacitated_until: int | None = None,
    ) -> None:
        """Correct stored round facts without manufacturing a combat action."""
        self.turn_state = turn_state
        self.waited = waited
        self._incapacitated_until = incapacitated_until
        self.last_action = last_action
        self._conditions = conditions.copy()
        self._forfeit_next_turn = forfeit_next_turn
        if self._round_started and turn_state is not TurnState.ACTED:
            self._reaction_dm = reaction_dm
            self._next_reaction_dm = 0
        else:
            self._reaction_dm = 0
            self._next_reaction_dm = reaction_dm

    @property
    def has_had_their_turn(self) -> bool:
        """True once they have acted or explicitly declined for now."""
        return self.turn_state is TurnState.ACTED or self.waited

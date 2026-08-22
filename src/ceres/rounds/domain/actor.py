"""Anyone taking turns: a PC, an NPC, an animal.

Called an actor rather than a combatant because a situation run in rounds need
not be a fight — it may be a fire, or a hull breach being patched against the
clock.
"""

from enum import StrEnum, auto
from typing import TYPE_CHECKING

from ceres.character.domain.characteristics import Chars
from ceres.rounds.domain.actions import ReactionKind
from ceres.rounds.domain.tracks import CharacteristicTrack, DamageTrack

if TYPE_CHECKING:
    from ceres.rounds.domain.situation import Party


class TurnState(StrEnum):
    """Where an actor stands in the current round."""

    PENDING = auto()  # their initiative step has not been reached
    READY = auto()  # green: may act now, including after waiting
    ACTED = auto()  # grey: done until the next round


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
    def is_able_to_act(self) -> bool:
        """Whether injury or stun permits this actor to take a turn."""
        return not (self.track.is_dead or self.track.is_unconscious or self.track.is_incapacitated)

    @property
    def can_act(self) -> bool:
        return self.turn_state is TurnState.READY and self.is_able_to_act

    @property
    def reaction_dm(self) -> int:
        """Penalty on the next turn that has not already been finished."""
        if self._round_started and self.turn_state is not TurnState.ACTED:
            return self._reaction_dm
        return self._next_reaction_dm

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
        self.track.round_passed()

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

    @property
    def has_had_their_turn(self) -> bool:
        """True once they have acted or explicitly declined for now."""
        return self.turn_state is TurnState.ACTED or self.waited

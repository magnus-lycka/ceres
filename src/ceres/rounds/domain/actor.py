"""Anyone taking turns: a PC, an NPC, an animal.

Called an actor rather than a combatant because a situation run in rounds need
not be a fight — it may be a fire, or a hull breach being patched against the
clock.
"""

from enum import StrEnum, auto
from typing import TYPE_CHECKING

from ceres.character.domain.characteristics import Chars
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
        self.reaction_dm = 0
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
    def can_act(self) -> bool:
        if self.turn_state is not TurnState.READY:
            return False
        return not (self.track.is_dead or self.track.is_unconscious or self.track.is_incapacitated)

    def begin_round(self) -> None:
        self.turn_state = TurnState.PENDING
        self.waited = False
        self.track.round_passed()

    def make_ready(self) -> None:
        if self.turn_state is TurnState.PENDING:
            self.turn_state = TurnState.READY
            self.waited = False

    def act(self) -> None:
        self.turn_state = TurnState.ACTED
        self.waited = False
        self.reaction_dm = 0

    def wait(self) -> None:
        """Delay the action until later in the turn (:32); stays green."""
        self.waited = True

    @property
    def has_had_their_turn(self) -> bool:
        """True once they have acted or explicitly declined for now."""
        return self.turn_state is TurnState.ACTED or self.waited

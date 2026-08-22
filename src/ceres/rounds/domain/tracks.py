"""How an actor absorbs damage.

What varies between actors is not how they take turns but how they are hurt, so
an actor *has a* damage track rather than being a subclass of one. Travellers
and NPCs use a `CharacteristicTrack`; animals use a `HitsTrack`.
"""

from abc import ABC, abstractmethod

from ceres.character.domain.characteristics import Chars, characteristic_dm
from ceres.rounds.domain.damage import DamageKind


class DamageTrack(ABC):
    """Knows how much punishment its owner has taken and what that means."""

    def apply(self, points: int, kind: DamageKind) -> None:
        if points <= 0:
            return
        if kind is DamageKind.STUN:
            self._apply_stun(points)
        else:
            self._apply_lethal(points)

    @abstractmethod
    def round_passed(self) -> None:
        """Advance any countdown the track maintains."""

    @abstractmethod
    def _apply_lethal(self, points: int) -> None: ...

    @abstractmethod
    def _apply_stun(self, points: int) -> None: ...

    @property
    @abstractmethod
    def is_unconscious(self) -> bool: ...

    @property
    @abstractmethod
    def is_dead(self) -> bool: ...

    @property
    @abstractmethod
    def is_incapacitated(self) -> bool:
        """Put out of action by stun rather than by injury."""


class CharacteristicTrack(DamageTrack):
    """STR, DEX and END, eroded by damage (refs/core/03_combat.md:259-268).

    Lethal and stun damage reduce the same END score; the two are kept apart
    only so that an hour of rest can restore the stun points and not the lethal
    ones. No threshold may branch on which bucket a point came from, except
    death, which stun can never cause. See docs/RULE_INTERPRETATIONS.md.
    """

    def __init__(self, *, strength: int, dexterity: int, endurance: int, excess_to: Chars = Chars.DEX):
        self._maximum = {Chars.STR: strength, Chars.DEX: dexterity, Chars.END: endurance}
        self._lethal = {Chars.STR: 0, Chars.DEX: 0, Chars.END: 0}
        self._stun_points = 0
        self._incapacitated_rounds = 0
        self.excess_to = excess_to

    def maximum(self, characteristic: Chars) -> int:
        return self._maximum[characteristic]

    def current(self, characteristic: Chars) -> int:
        value = self._maximum[characteristic] - self._lethal[characteristic]
        if characteristic is Chars.END:
            value -= self._stun_points
        return max(value, 0)

    def dm(self, characteristic: Chars) -> int:
        return characteristic_dm(self.current(characteristic))

    @property
    def stun_points(self) -> int:
        return self._stun_points

    @property
    def incapacitated_rounds(self) -> int:
        return self._incapacitated_rounds

    def round_passed(self) -> None:
        if self._incapacitated_rounds > 0:
            self._incapacitated_rounds -= 1

    def rest_one_hour(self) -> None:
        """Stun damage is completely healed by one hour of rest (:366)."""
        self._stun_points = 0
        self._incapacitated_rounds = 0

    def _apply_lethal(self, points: int) -> None:
        for characteristic in self._drain_order():
            if points <= 0:
                return
            absorbed = min(points, self.current(characteristic))
            self._take_lethal(characteristic, absorbed)
            points -= absorbed
        if points > 0:
            self._take_lethal(Chars.END, min(points, self._lethal_room(Chars.END)))

    def _lethal_room(self, characteristic: Chars) -> int:
        """How much more lethal damage this characteristic can still absorb."""
        return self._maximum[characteristic] - self._lethal[characteristic]

    def _take_lethal(self, characteristic: Chars, points: int) -> None:
        """Record lethal damage, displacing any stun that was occupying END.

        Once every characteristic reads zero, the cascade has nowhere left to
        put damage, yet stun may still be sitting on END capacity that lethal
        damage has never claimed. It claims it here: stun is allowed to bring
        unconsciousness forward, but it must never be the thing standing
        between an actor and death (RIC-011, RIC-012).
        """
        self._lethal[characteristic] += points
        if characteristic is Chars.END:
            self._stun_points = min(self._stun_points, self._lethal_room(Chars.END))

    def _drain_order(self) -> tuple[Chars, ...]:
        """END first, then the target's choice of STR or DEX, then the other."""
        spare = Chars.STR if self.excess_to is Chars.DEX else Chars.DEX
        return Chars.END, self.excess_to, spare

    def _apply_stun(self, points: int) -> None:
        endurance = self.current(Chars.END)
        self._stun_points += min(points, endurance)
        if points >= endurance:
            self._incapacitated_rounds = max(self._incapacitated_rounds, points - endurance)

    @property
    def is_unconscious(self) -> bool:
        """Unconscious once STR or DEX is exhausted (:265). END alone does not."""
        return self.current(Chars.STR) == 0 or self.current(Chars.DEX) == 0

    @property
    def is_incapacitated(self) -> bool:
        return self._incapacitated_rounds > 0

    @property
    def is_dead(self) -> bool:
        """All three physical characteristics at 0 (:266), by lethal damage only.

        Stun damage is explicitly non-lethal (:366), so END suppressed by a
        stunner cannot be the point that finishes someone off.
        """
        return all(self._maximum[c] - self._lethal[c] <= 0 for c in (Chars.STR, Chars.DEX, Chars.END))


class HitsTrack(DamageTrack):
    """A single Hits score, as animals use (refs/core/03_combat.md:604, 652-660)."""

    def __init__(self, *, hits: int):
        self._maximum = hits
        self._damage = 0
        self._stun_total = 0

    @property
    def maximum(self) -> int:
        return self._maximum

    @property
    def current(self) -> int:
        """Allowed to go negative: destruction is measured below zero (:660)."""
        return self._maximum - self._damage

    @property
    def stun_total(self) -> int:
        return self._stun_total

    def round_passed(self) -> None:
        """Nothing to count down: the animal stun rule states no duration (:604)."""

    def _apply_lethal(self, points: int) -> None:
        self._damage += points

    def _apply_stun(self, points: int) -> None:
        """Stun accumulates separately and never reduces Hits (:604)."""
        self._stun_total += points

    @property
    def is_dead(self) -> bool:
        return self.current <= 0

    @property
    def is_unconscious(self) -> bool:
        """Reduced to a tenth of starting Hits or less (:658)."""
        return 0 < self.current * 10 <= self._maximum

    @property
    def may_be_driven_off(self) -> bool:
        """Half Hits or less, at the referee's option (:656). Never automatic."""
        return 0 < self.current * 2 <= self._maximum

    @property
    def is_destroyed(self) -> bool:
        """Body destroyed at negative starting Hits or worse (:660)."""
        return self.current <= -self._maximum

    @property
    def is_incapacitated(self) -> bool:
        """A stun weapon incapacitates at cumulative half Hits (:604)."""
        return self._stun_total * 2 >= self._maximum

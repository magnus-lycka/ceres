"""How an actor absorbs damage.

What varies between actors is not how they take turns but how they are hurt, so
an actor *has a* damage track rather than being a subclass of one. Travellers
and NPCs use a `CharacteristicTrack`; animals use a `HitsTrack`.
"""

from abc import ABC, abstractmethod

from ceres.character.domain.characteristics import Chars, characteristic_dm
from ceres.rounds.domain.damage import DamageKind

PHYSICAL_CHARACTERISTICS = (Chars.STR, Chars.DEX, Chars.END)


class DamageTrack(ABC):
    """Knows how much punishment its owner has taken and what that means."""

    def __init__(self) -> None:
        self._stun_points = 0
        self._incapacitated_rounds = 0

    def apply(self, points: int, kind: DamageKind) -> None:
        if points <= 0:
            return
        if kind is DamageKind.STUN:
            self._apply_stun(points)
        else:
            self._apply_lethal(points)

    def round_passed(self) -> None:
        """Advance any countdown the track maintains."""
        if self._incapacitated_rounds > 0:
            self._incapacitated_rounds -= 1

    def rest_one_hour(self) -> None:
        """Clear damage received from Stun weapons (:366)."""
        self._stun_points = 0
        self._incapacitated_rounds = 0

    def _apply_stun_with_room(self, points: int, room: int) -> None:
        """Store stun up to a track-specific floor; overflow becomes rounds."""
        absorbed = min(points, room)
        self._stun_points += absorbed
        overflow = points - absorbed
        self._incapacitated_rounds = max(self._incapacitated_rounds, overflow)

    @staticmethod
    def _validate_stun_state(stun_points: int, incapacitated_rounds: int) -> None:
        if stun_points < 0 or incapacitated_rounds < 0:
            msg = 'stun points and rounds cannot be negative'
            raise ValueError(msg)

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

    @property
    def stun_points(self) -> int:
        """Stun damage currently suppressing the track's damage-bearing stat."""
        return self._stun_points

    @property
    def incapacitated_rounds(self) -> int:
        """Rounds of stun overflow remaining."""
        return self._incapacitated_rounds


class CharacteristicTrack(DamageTrack):
    """STR, DEX and END, eroded by damage (refs/core/03_combat.md:259-268).

    Lethal and stun damage reduce the same END score; the two are kept apart
    only so that an hour of rest can restore the stun points and not the lethal
    ones. No threshold may branch on which bucket a point came from, except
    death, which stun can never cause. See docs/RULE_INTERPRETATIONS.md.
    """

    def __init__(self, *, strength: int, dexterity: int, endurance: int, excess_to: Chars = Chars.DEX):
        super().__init__()
        self._maximum = {Chars.STR: strength, Chars.DEX: dexterity, Chars.END: endurance}
        self._lethal = {Chars.STR: 0, Chars.DEX: 0, Chars.END: 0}
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

    def correct_state(
        self,
        *,
        maximum: dict[Chars, int],
        current: dict[Chars, int],
        stun_points: int,
        incapacitated_rounds: int,
    ) -> None:
        """Replace the editable state from the values shown to the referee."""
        self._validate_stun_state(stun_points, incapacitated_rounds)
        if any(maximum[characteristic] <= 0 for characteristic in PHYSICAL_CHARACTERISTICS):
            msg = 'maximum characteristics must be positive'
            raise ValueError(msg)
        if any(
            not 0 <= current[characteristic] <= maximum[characteristic] for characteristic in PHYSICAL_CHARACTERISTICS
        ):
            msg = 'current characteristics must be between zero and their maximum'
            raise ValueError(msg)
        if current[Chars.END] + stun_points > maximum[Chars.END]:
            msg = 'current END plus stun points cannot exceed maximum END'
            raise ValueError(msg)

        self._maximum = {characteristic: maximum[characteristic] for characteristic in PHYSICAL_CHARACTERISTICS}
        self._lethal = {
            characteristic: maximum[characteristic] - current[characteristic]
            for characteristic in PHYSICAL_CHARACTERISTICS
        }
        self._lethal[Chars.END] -= stun_points
        self._stun_points = stun_points
        self._incapacitated_rounds = incapacitated_rounds

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
        self._apply_stun_with_room(points, self.current(Chars.END))

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
    """Animal Hits, including the shared stun contract defined by RIC-015."""

    def __init__(self, *, hits: int):
        super().__init__()
        self._maximum = hits
        self._damage = 0

    @property
    def maximum(self) -> int:
        return self._maximum

    @property
    def current(self) -> int:
        """Allowed to go negative: destruction is measured below zero (:660)."""
        return self._lethal_current - self._stun_points

    @property
    def _lethal_current(self) -> int:
        return self._maximum - self._damage

    @property
    def _stun_floor(self) -> int:
        """Stun can suppress Hits to half their starting value, rounded down."""
        return self._maximum // 2

    def _stun_room(self) -> int:
        """How many stun points can still suppress Hits before overflow."""
        return max(self._lethal_current - self._stun_floor - self._stun_points, 0)

    def correct_state(
        self,
        *,
        maximum: int,
        current: int,
        stun_points: int,
        incapacitated_rounds: int,
    ) -> None:
        """Replace the editable state from the values shown to the referee."""
        self._validate_stun_state(stun_points, incapacitated_rounds)
        if maximum <= 0:
            msg = 'maximum Hits must be positive'
            raise ValueError(msg)
        if current > maximum:
            msg = 'current Hits cannot exceed maximum Hits'
            raise ValueError(msg)

        lethal_current = current + stun_points
        maximum_stun = max(lethal_current - maximum // 2, 0)
        if stun_points > maximum_stun:
            msg = 'stun points cannot suppress Hits below half maximum'
            raise ValueError(msg)

        self._maximum = maximum
        self._damage = maximum - lethal_current
        self._stun_points = stun_points
        self._incapacitated_rounds = incapacitated_rounds

    def _apply_lethal(self, points: int) -> None:
        self._damage += points
        maximum_stun = max(self._lethal_current - self._stun_floor, 0)
        self._stun_points = min(self._stun_points, maximum_stun)

    def _apply_stun(self, points: int) -> None:
        """Suppress Hits to half; excess determines incapacitation rounds."""
        self._apply_stun_with_room(points, self._stun_room())

    @property
    def is_dead(self) -> bool:
        return self._lethal_current <= 0

    @property
    def is_unconscious(self) -> bool:
        """Reduced to a tenth of starting Hits or less (:658)."""
        return 0 < self._lethal_current * 10 <= self._maximum

    @property
    def may_be_driven_off(self) -> bool:
        """Half Hits or less, at the referee's option (:656). Never automatic."""
        return 0 < self.current * 2 <= self._maximum

    @property
    def is_destroyed(self) -> bool:
        """Body destroyed at negative starting Hits or worse (:660)."""
        return self._lethal_current <= -self._maximum

    @property
    def is_incapacitated(self) -> bool:
        return self._incapacitated_rounds > 0

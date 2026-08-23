"""How an actor absorbs damage.

What varies between actors is not how they take turns but how they are hurt, so
an actor *has a* damage track rather than being a subclass of one. Travellers
and NPCs use a `CharacteristicTrack`; animals use a `HitsTrack`.

A track keeps an ordered history of injuries rather than running totals. Current
values are the maximum less what the history records, so the rules are never
replayed to answer a question, and the first-aid view — which injury is still
inside the one-minute window — reads the same history.
"""

from abc import ABC, abstractmethod

from ceres.character.domain.characteristics import Chars, characteristic_dm
from ceres.rounds.domain.damage import CharacteristicInjury, DamageKind, HitsInjury, Injury

PHYSICAL_CHARACTERISTICS = (Chars.STR, Chars.DEX, Chars.END)


class DamageTrack[I: Injury](ABC):
    """Knows how much punishment its owner has taken and what that means."""

    def __init__(self) -> None:
        self._injuries: list[I] = []

    @property
    def injuries(self) -> tuple[I, ...]:
        """The history, oldest first: the first-aid view reads this."""
        return tuple(self._injuries)

    def apply(self, points: int, kind: DamageKind, *, at: int | None = None) -> int:
        """Take `points` of damage in round `at`, and record what it cost.

        Returns the rounds of incapacitation the hit caused, which is a fact
        about the fight rather than about the body: the situation membership
        holds it, because only a fight counts rounds.
        """
        if points <= 0:
            return 0
        if kind is DamageKind.STUN:
            return self._apply_stun(points, at)
        self._apply_lethal(points, at)
        return 0

    def clear_stun(self) -> None:
        """Clear damage received from Stun weapons (:366).

        The rule is an hour of rest, which happens between fights rather than
        between rounds, so the referee applies it rather than the app inferring
        it. Lethal injuries are untouched.
        """
        self._injuries = [injury for injury in self._injuries if injury.kind is not DamageKind.STUN]

    def carry_over(self) -> None:
        """End the situation: injuries survive it, their round numbers do not."""
        self._injuries = [self._as_earlier(injury) for injury in self._injuries]

    @property
    def stun_points(self) -> int:
        """Stun damage currently suppressing the track's damage-bearing stat."""
        return sum(injury.total for injury in self._injuries if injury.kind is DamageKind.STUN)

    def _record(self, injury: I) -> None:
        """Keep a hit only if it actually took something off."""
        if injury.total > 0:
            self._injuries.append(injury)

    @staticmethod
    def _absorb_stun(points: int, room: int) -> tuple[int, int]:
        """Split a stun hit into what it suppresses and what overflows (:366)."""
        absorbed = min(points, max(room, 0))
        return absorbed, points - absorbed

    def _displace_stun_beyond(self, capacity: int) -> None:
        """Give up stun that lethal damage has claimed, oldest hit first.

        Stun is allowed to bring unconsciousness forward, but it must never be
        the thing standing between an actor and death (RIC-011, RIC-012).
        """
        excess = self.stun_points - max(capacity, 0)
        if excess <= 0:
            return
        kept: list[I] = []
        for injury in self._injuries:
            if injury.kind is not DamageKind.STUN or excess <= 0:
                kept.append(injury)
                continue
            removed = min(excess, injury.total)
            excess -= removed
            standing = injury.shrunk_by(removed)
            if standing.total > 0:
                kept.append(standing)
        self._injuries = kept

    @staticmethod
    def _validate_stun_points(stun_points: int) -> None:
        if stun_points < 0:
            msg = 'stun points cannot be negative'
            raise ValueError(msg)

    @staticmethod
    @abstractmethod
    def _as_earlier(injury: I) -> I:
        """The same injury with its round forgotten."""

    @abstractmethod
    def _apply_lethal(self, points: int, at: int | None) -> None: ...

    @abstractmethod
    def _apply_stun(self, points: int, at: int | None) -> int:
        """Record what the hit suppressed; return the rounds it overflowed by."""

    @property
    @abstractmethod
    def is_unconscious(self) -> bool: ...

    @property
    @abstractmethod
    def is_dead(self) -> bool: ...


class CharacteristicTrack(DamageTrack[CharacteristicInjury]):
    """STR, DEX and END, eroded by damage (refs/core/03_combat.md:259-268).

    Lethal and stun damage reduce the same END score; the two are told apart
    only so that Clear stun can restore the stun points and not the lethal ones.
    No threshold may branch on which kind a point came from, except death, which
    stun can never cause. See docs/RULE_INTERPRETATIONS.md.
    """

    def __init__(self, *, strength: int, dexterity: int, endurance: int, excess_to: Chars = Chars.DEX):
        super().__init__()
        self._maximum = {Chars.STR: strength, Chars.DEX: dexterity, Chars.END: endurance}
        self.excess_to = excess_to

    def maximum(self, characteristic: Chars) -> int:
        return self._maximum[characteristic]

    def current(self, characteristic: Chars) -> int:
        value = self._maximum[characteristic] - self._lethal(characteristic)
        if characteristic is Chars.END:
            value -= self.stun_points
        return max(value, 0)

    def dm(self, characteristic: Chars) -> int:
        return characteristic_dm(self.current(characteristic))

    def correct_state(
        self,
        *,
        maximum: dict[Chars, int],
        current: dict[Chars, int],
        stun_points: int,
    ) -> None:
        """Replace the editable state from the values shown to the referee.

        A corrected total has no per-round provenance, so it lands as a single
        injury stamped earlier — which is what it is: damage of unknown age.
        """
        self._validate_stun_points(stun_points)
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
        lethal = {
            characteristic: maximum[characteristic] - current[characteristic]
            for characteristic in PHYSICAL_CHARACTERISTICS
        }
        lethal[Chars.END] -= stun_points
        self._injuries = []
        self._record(
            CharacteristicInjury(
                kind=DamageKind.LETHAL,
                reductions={characteristic: points for characteristic, points in lethal.items() if points > 0},
            )
        )
        self._record(CharacteristicInjury(kind=DamageKind.STUN, reductions={Chars.END: stun_points}))

    def _lethal(self, characteristic: Chars) -> int:
        return sum(injury.reduction_to(characteristic) for injury in self._injuries if injury.kind is DamageKind.LETHAL)

    def _apply_lethal(self, points: int, at: int | None) -> None:
        reductions: dict[Chars, int] = {}
        for characteristic in self._drain_order():
            if points <= 0:
                break
            absorbed = min(points, self.current(characteristic))
            if absorbed > 0:
                reductions[characteristic] = absorbed
            points -= absorbed
        if points > 0:
            spill = min(points, self._lethal_room(Chars.END) - reductions.get(Chars.END, 0))
            if spill > 0:
                reductions[Chars.END] = reductions.get(Chars.END, 0) + spill
        self._record(CharacteristicInjury(kind=DamageKind.LETHAL, when=at, reductions=reductions))
        self._displace_stun_beyond(self._lethal_room(Chars.END))

    def _lethal_room(self, characteristic: Chars) -> int:
        """How much more lethal damage this characteristic can still absorb."""
        return self._maximum[characteristic] - self._lethal(characteristic)

    def _drain_order(self) -> tuple[Chars, ...]:
        """END first, then the target's choice of STR or DEX, then the other."""
        spare = Chars.STR if self.excess_to is Chars.DEX else Chars.DEX
        return Chars.END, self.excess_to, spare

    def _apply_stun(self, points: int, at: int | None) -> int:
        absorbed, overflow = self._absorb_stun(points, self.current(Chars.END))
        self._record(CharacteristicInjury(kind=DamageKind.STUN, when=at, reductions={Chars.END: absorbed}))
        return overflow

    @staticmethod
    def _as_earlier(injury: CharacteristicInjury) -> CharacteristicInjury:
        return CharacteristicInjury(kind=injury.kind, reductions=dict(injury.reductions))

    @property
    def is_unconscious(self) -> bool:
        """Unconscious once STR or DEX is exhausted (:265). END alone does not."""
        return self.current(Chars.STR) == 0 or self.current(Chars.DEX) == 0

    @property
    def is_dead(self) -> bool:
        """All three physical characteristics at 0 (:266), by lethal damage only.

        Stun damage is explicitly non-lethal (:366), so END suppressed by a
        stunner cannot be the point that finishes someone off.
        """
        return all(self._lethal_room(characteristic) <= 0 for characteristic in PHYSICAL_CHARACTERISTICS)


class HitsTrack(DamageTrack[HitsInjury]):
    """Animal Hits, including the shared stun contract defined by RIC-015."""

    def __init__(self, *, hits: int):
        super().__init__()
        self._maximum = hits

    @property
    def maximum(self) -> int:
        return self._maximum

    @property
    def current(self) -> int:
        """Allowed to go negative: destruction is measured below zero (:660)."""
        return self._lethal_current - self.stun_points

    @property
    def _lethal_current(self) -> int:
        damage = sum(injury.total for injury in self._injuries if injury.kind is DamageKind.LETHAL)
        return self._maximum - damage

    @property
    def _stun_floor(self) -> int:
        """Stun can suppress Hits to half their starting value, rounded down."""
        return self._maximum // 2

    @property
    def _stun_capacity(self) -> int:
        """The most stun that may stand against the current Hits."""
        return max(self._lethal_current - self._stun_floor, 0)

    def correct_state(
        self,
        *,
        maximum: int,
        current: int,
        stun_points: int,
    ) -> None:
        """Replace the editable state from the values shown to the referee."""
        self._validate_stun_points(stun_points)
        if maximum <= 0:
            msg = 'maximum Hits must be positive'
            raise ValueError(msg)
        if current > maximum:
            msg = 'current Hits cannot exceed maximum Hits'
            raise ValueError(msg)

        lethal_current = current + stun_points
        if stun_points > max(lethal_current - maximum // 2, 0):
            msg = 'stun points cannot suppress Hits below half maximum'
            raise ValueError(msg)

        self._maximum = maximum
        self._injuries = []
        self._record(HitsInjury(kind=DamageKind.LETHAL, reduction=maximum - lethal_current))
        self._record(HitsInjury(kind=DamageKind.STUN, reduction=stun_points))

    def _apply_lethal(self, points: int, at: int | None) -> None:
        self._record(HitsInjury(kind=DamageKind.LETHAL, when=at, reduction=points))
        self._displace_stun_beyond(self._stun_capacity)

    def _apply_stun(self, points: int, at: int | None) -> int:
        """Suppress Hits to half; excess determines incapacitation rounds."""
        absorbed, overflow = self._absorb_stun(points, self._stun_capacity - self.stun_points)
        self._record(HitsInjury(kind=DamageKind.STUN, when=at, reduction=absorbed))
        return overflow

    @staticmethod
    def _as_earlier(injury: HitsInjury) -> HitsInjury:
        return HitsInjury(kind=injury.kind, reduction=injury.reduction)

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

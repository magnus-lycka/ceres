"""Damage as it is recorded: what each hit actually did, and when."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Self

from ceres.character.domain.characteristics import Chars


class DamageKind(StrEnum):
    """The two kinds of damage a damage track can absorb.

    Lethal damage erodes characteristics permanently until healed. Stun damage
    is deducted from END only and is cleared by an hour of rest
    (refs/core/03_combat.md:366).
    """

    LETHAL = 'lethal'
    STUN = 'stun'


@dataclass(frozen=True, kw_only=True)
class Injury(ABC):
    """One hit, stored as the reduction it caused rather than as its roll.

    Which characteristic absorbed how much is settled when the damage lands, so
    that is what is kept. Nothing has to be replayed to know a current value,
    and the referee corrects the line that was wrong rather than a total.

    ``when`` is the round of the situation the hit landed in, or ``None`` once
    that situation has ended. Injuries carried out of a fight are past the
    one-minute first-aid window in any case, so their round has no further use.
    """

    kind: DamageKind
    when: int | None = None

    @property
    def is_earlier(self) -> bool:
        return self.when is None

    def rounds_ago(self, current_round: int) -> int | None:
        """How long ago this landed, for the first-aid view. None if earlier."""
        return None if self.when is None else current_round - self.when

    @property
    @abstractmethod
    def total(self) -> int:
        """Everything this hit currently takes off, across all stats."""

    @abstractmethod
    def shrunk_by(self, points: int) -> Self:
        """A copy standing for ``points`` less, when lethal damage displaces it."""


@dataclass(frozen=True, kw_only=True)
class CharacteristicInjury(Injury):
    """What one hit took off STR, DEX and END."""

    reductions: Mapping[Chars, int]

    @property
    def total(self) -> int:
        return sum(self.reductions.values())

    def reduction_to(self, characteristic: Chars) -> int:
        return self.reductions.get(characteristic, 0)

    def shrunk_by(self, points: int) -> Self:
        """Only stun is ever displaced, and stun only ever sits on END (:366)."""
        remaining = self.reduction_to(Chars.END) - points
        return replace(self, reductions={Chars.END: remaining} if remaining > 0 else {})


@dataclass(frozen=True, kw_only=True)
class HitsInjury(Injury):
    """What one hit took off an animal's Hits."""

    reduction: int

    @property
    def total(self) -> int:
        return self.reduction

    def shrunk_by(self, points: int) -> Self:
        return replace(self, reduction=self.reduction - points)

from enum import StrEnum


class DamageKind(StrEnum):
    """The two kinds of damage a damage track can absorb.

    Lethal damage erodes characteristics permanently until healed. Stun damage
    is deducted from END only and is cleared by an hour of rest
    (refs/core/03_combat.md:366).
    """

    LETHAL = 'lethal'
    STUN = 'stun'

from enum import StrEnum


class Chars(StrEnum):
    STR = 'STR'
    DEX = 'DEX'
    END = 'END'
    INT = 'INT'
    EDU = 'EDU'
    SOC = 'SOC'
    CHA = 'CHA'
    PSI = 'PSI'


class ConnectionKind(StrEnum):
    CONTACT = 'connection_contact'
    ALLY = 'connection_ally'
    RIVAL = 'connection_rival'
    ENEMY = 'connection_enemy'


# Default UCP order for Humaniti/Vilani. Per-sophont order is defined in the sophont object.
UCP_STATS: tuple[Chars, ...] = (Chars.STR, Chars.DEX, Chars.END, Chars.INT, Chars.EDU, Chars.SOC)


def characteristic_dm(value: int) -> int:
    if value <= 0:
        return -3
    return value // 3 - 2

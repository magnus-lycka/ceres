from enum import StrEnum


class Chars(StrEnum):
    STR = 'STR'
    DEX = 'DEX'
    END = 'END'
    INT = 'INT'
    EDU = 'EDU'
    SOC = 'SOC'


class ConnectionKind(StrEnum):
    CONTACT = 'contact'
    ALLY = 'ally'
    RIVAL = 'rival'
    ENEMY = 'enemy'


UCP_STATS: tuple[Chars, ...] = tuple(Chars)


def characteristic_dm(value: int) -> int:
    if value <= 0:
        return -3
    return value // 3 - 2

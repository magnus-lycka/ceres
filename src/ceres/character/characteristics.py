from enum import StrEnum


class Chars(StrEnum):
    STR = 'STR'
    DEX = 'DEX'
    END = 'END'
    INT = 'INT'
    EDU = 'EDU'
    SOC = 'SOC'


UCP_STATS: tuple[Chars, ...] = tuple(Chars)

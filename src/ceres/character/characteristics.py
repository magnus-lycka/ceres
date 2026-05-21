from enum import StrEnum, auto


class Chars(StrEnum):
    STR = auto()
    DEX = auto()
    END = auto()
    INT = auto()
    EDU = auto()
    SOC = auto()


UCP_STATS: tuple[str, ...] = tuple(c.name for c in Chars)

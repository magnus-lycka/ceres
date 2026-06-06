from dataclasses import dataclass

from ceres.character.domain.characteristics import Chars


@dataclass(frozen=True)
class Sophont:
    name: str
    ucp_stats: tuple[Chars, ...]


_HUMANITI_UCP = (Chars.STR, Chars.DEX, Chars.END, Chars.INT, Chars.EDU, Chars.SOC)

HUMANITI = Sophont(name='Humaniti', ucp_stats=_HUMANITI_UCP)
VILANI = Sophont(name='Vilani', ucp_stats=_HUMANITI_UCP)

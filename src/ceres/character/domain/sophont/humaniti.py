from dataclasses import dataclass

from ceres.adapters.travellermap import TravellerMapWorld
from ceres.character.domain.characteristics import Chars


@dataclass(frozen=True)
class Sophont:
    name: str
    ucp_stats: tuple[Chars, ...] = (Chars.STR, Chars.DEX, Chars.END, Chars.INT, Chars.EDU, Chars.SOC)
    allegiance_pattern: str | None = None
    remarks_codes: tuple[str, ...] = ()

    def available_at(self, world: TravellerMapWorld) -> bool:
        return self._allegiance_matches(world) or self._remarks_match(world)

    def _allegiance_matches(self, world: TravellerMapWorld) -> bool:
        if self.allegiance_pattern is None:
            return False
        if self.allegiance_pattern == '*':
            return True
        if self.allegiance_pattern.endswith('*'):
            return world.allegiance.startswith(self.allegiance_pattern[:-1])
        return world.allegiance == self.allegiance_pattern

    def _remarks_match(self, world: TravellerMapWorld) -> bool:
        if not self.remarks_codes:
            return False
        words = world.remarks.split()
        return any(word.startswith(code) for code in self.remarks_codes for word in words)


HUMANITI = Sophont(name='Humaniti', allegiance_pattern='*')
VILANI = Sophont(name='Vilani', allegiance_pattern='Im*')
DARMINE = Sophont(name='Darmine', remarks_codes=('Darm', '(Darmine)'))
LIBERTS = Sophont(name='Liberts', remarks_codes=('Libe', '(Liberts)'))
MURRISSI = Sophont(name='Murrissi', remarks_codes=('Murr', '(Murrissi)'))
LANCIANS = Sophont(name='Lancians', remarks_codes=('Lanc', '(Lancians)'))
SWANFEI = Sophont(name='Swanfei', remarks_codes=('Swan', '(Swanfeh)'))
URUNISHANI = Sophont(name='Urunishani', remarks_codes=('Urun', '(Urunishani)'))

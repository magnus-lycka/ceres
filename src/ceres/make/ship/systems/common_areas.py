from typing import ClassVar, Literal

from pydantic import Field

from ceres.shared import NoteList, _Note

from ..parts import ShipPart
from .common import _ExplicitTonsSystemPart, _ZeroPowerSystemPart


class CommonArea(_ExplicitTonsSystemPart):
    description: Literal['Common Area'] = 'Common Area'
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def cost(self) -> float:
        return self.tons * 100_000.0

    @property
    def power(self) -> float:
        return 0.0


class CommercialZone(_ExplicitTonsSystemPart):
    system_type: Literal['COMMERCIAL_ZONE'] = 'COMMERCIAL_ZONE'
    description: Literal['Commercial Zone'] = 'Commercial Zone'
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0

    @property
    def power(self) -> float:
        return float(max(1, int(self.tons // 200)))


class MultiEnvironmentSpace(ShipPart):
    system_type: Literal['MULTI_ENVIRONMENT_SPACE'] = 'MULTI_ENVIRONMENT_SPACE'
    description: Literal['Multi-Environment Space'] = 'Multi-Environment Space'
    covered_tons: float
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def item_description(self) -> str:
        return f'Multi-Environment Space ({self.covered_tons:g} tons)'

    @property
    def tons(self) -> float:
        return self.covered_tons * 0.05

    @property
    def cost(self) -> float:
        return self.tons * 500_000.0

    @property
    def power(self) -> float:
        return self.tons

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Support equipment for modifying a designated area to unusual environmental conditions')
        return notes


class SwimmingPool(CommonArea):
    description: Literal['Swimming Pool'] = 'Swimming Pool'

    @property
    def cost(self) -> float:
        return self.tons * 20_000.0


class Theatre(CommonArea):
    description: Literal['Theatre'] = 'Theatre'
    advanced: bool = False

    @property
    def cost(self) -> float:
        if self.advanced:
            return self.tons * 200_000.0
        return self.tons * 100_000.0


class Brewery(ShipPart):
    system_type: Literal['BREWERY'] = 'BREWERY'
    description: Literal['Brewery'] = 'Brewery'
    tl: int = 10
    litres_per_week: float
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def item_description(self) -> str:
        return f'Brewery ({self.litres_per_week:g} litres/week)'

    @property
    def tons(self) -> float:
        return self.litres_per_week / 20.0

    @property
    def cost(self) -> float:
        return self.tons * 100_000.0

    @property
    def power(self) -> float:
        return 0.0


class GourmetKitchen(ShipPart):
    system_type: Literal['GOURMET_KITCHEN'] = 'GOURMET_KITCHEN'
    description: Literal['Gourmet Kitchen'] = 'Gourmet Kitchen'
    diners: int
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def item_description(self) -> str:
        diner_label = 'diner' if self.diners == 1 else 'diners'
        return f'Gourmet Kitchen ({self.diners} {diner_label})'

    @property
    def tons(self) -> float:
        return float(self.diners)

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0

    @property
    def power(self) -> float:
        return 0.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Requires Steward 2 to use properly')
        notes.info('DM +1 when seeking high passengers')
        return notes


class ZeroGRoom(CommonArea):
    system_type: Literal['ZERO_G_ROOM'] = 'ZERO_G_ROOM'
    description: Literal['Zero-G Room'] = 'Zero-G Room'
    cost: ClassVar[float]

    @property
    def cost(self) -> float:
        return 50_000.0

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('Includes controls and safe-access portal')
        return notes


class WetBar(_ZeroPowerSystemPart):
    description: Literal['Wet Bar'] = 'Wet Bar'
    tons: ClassVar[float]
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        return 2_000.0


class HotTub(CommonArea):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    base_tons: float = Field(0.0, alias='tons', exclude=True)
    users: int = 1

    def item_description(self) -> str:
        label = 'User' if self.users == 1 else 'Users'
        return f'Hot Tub ({self.users} {label})'

    @property
    def tons(self) -> float:
        return self.users * 0.25

    @property
    def cost(self) -> float:
        return self.tons * 12_000.0

    @property
    def power(self) -> float:
        return 0.0

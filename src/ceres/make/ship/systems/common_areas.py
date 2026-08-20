from typing import ClassVar, Literal

from pydantic import ConfigDict, Field

from ceres.shared import NoteList, _Note

from ..parts import ShipPartBase, UnpoweredShipPart


class CommonArea(ShipPartBase):
    """Tonnage is supplied, but `HotTub` derives its own from `users`.

    A subclass cannot override an inherited field with a property, so the
    supplied value is stored under another name and exposed as a property the
    subclass may override. This indirection is needed only where a stored
    parent has a derived child.
    """

    base_tons: float = Field(0.0, alias='tons')
    model_config = ConfigDict(frozen=True, populate_by_name=True, serialize_by_alias=True)
    description: Literal['Common Area'] = 'Common Area'
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return self.base_tons

    @property
    def cost(self) -> float:
        return self.tons * 100_000.0

    @property
    def power(self) -> float:
        return 0.0


class CommercialZone(ShipPartBase):
    tons: float = 0.0
    system_type: Literal['COMMERCIAL_ZONE'] = 'COMMERCIAL_ZONE'
    description: Literal['Commercial Zone'] = 'Commercial Zone'
    cost: ClassVar[float]

    @property
    def cost(self) -> float:
        return self.tons * 200_000.0

    @property
    def power(self) -> float:
        return float(max(1, int(self.tons // 200)))


class MultiEnvironmentSpace(ShipPartBase):
    system_type: Literal['MULTI_ENVIRONMENT_SPACE'] = 'MULTI_ENVIRONMENT_SPACE'
    description: Literal['Multi-Environment Space'] = 'Multi-Environment Space'
    covered_tons: float
    cost: ClassVar[float]

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


class Brewery(ShipPartBase):
    system_type: Literal['BREWERY'] = 'BREWERY'
    description: Literal['Brewery'] = 'Brewery'
    tl: int = 10
    litres_per_week: float
    cost: ClassVar[float]

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


class GourmetKitchen(ShipPartBase):
    system_type: Literal['GOURMET_KITCHEN'] = 'GOURMET_KITCHEN'
    description: Literal['Gourmet Kitchen'] = 'Gourmet Kitchen'
    diners: int
    cost: ClassVar[float]

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


class WetBar(UnpoweredShipPart):
    description: Literal['Wet Bar'] = 'Wet Bar'
    cost: ClassVar[float]

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        return 2_000.0


class HotTub(CommonArea):
    cost: ClassVar[float]
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

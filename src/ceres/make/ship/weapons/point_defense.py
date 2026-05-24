from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import NoteList, _Note

from ..parts import CustomisableShipPart, ShipPart, SizeReduction
from .common import _GENERAL_WEAPON_MODIFICATIONS

PointDefenseKind = Literal['laser', 'gauss']
PointDefenseRating = Literal[1, 2, 3]


class _PointDefenseBattery(CustomisableShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    battery_type: str
    kind: ClassVar[PointDefenseKind]
    rating: ClassVar[PointDefenseRating]
    description: ClassVar[str]
    base_tons: ClassVar[float]
    base_cost: ClassVar[float]
    base_power: ClassVar[float]
    allowed_modifications: ClassVar[frozenset[str]] = _GENERAL_WEAPON_MODIFICATIONS | {SizeReduction.name}

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        intercept_dice = self.rating * 2
        notes.info(f'Intercept +{intercept_dice}D')
        if self.kind == 'gauss':
            notes.info('Requires ammunition storage to reload after 12 rounds')
        return notes

    @property
    def hardpoints_required(self) -> int:
        return 1

    @property
    def tons(self) -> float:
        return self.base_tons * self.tons_multiplier

    @property
    def cost(self) -> float:
        return self.base_cost * self.cost_multiplier

    @property
    def power(self) -> float:
        return self.base_power * self.power_multiplier


class LaserPointDefenseBattery1(_PointDefenseBattery):
    battery_type: Literal['laser_point_defense_1'] = 'laser_point_defense_1'
    kind: ClassVar[PointDefenseKind] = 'laser'
    rating: ClassVar[PointDefenseRating] = 1
    description = 'Point Defence Laser Battery Type I'
    tl: int = 10
    base_tons = 20.0
    base_power = 10.0
    base_cost = 5_000_000.0


class LaserPointDefenseBattery2(_PointDefenseBattery):
    battery_type: Literal['laser_point_defense_2'] = 'laser_point_defense_2'
    kind: ClassVar[PointDefenseKind] = 'laser'
    rating: ClassVar[PointDefenseRating] = 2
    description = 'Point Defence Laser Battery Type II'
    tl: int = 12
    base_tons = 20.0
    base_power = 20.0
    base_cost = 10_000_000.0


class LaserPointDefenseBattery3(_PointDefenseBattery):
    battery_type: Literal['laser_point_defense_3'] = 'laser_point_defense_3'
    kind: ClassVar[PointDefenseKind] = 'laser'
    rating: ClassVar[PointDefenseRating] = 3
    description = 'Point Defence Laser Battery Type III'
    tl: int = 14
    base_tons = 20.0
    base_power = 30.0
    base_cost = 20_000_000.0


class GaussPointDefenseBattery1(_PointDefenseBattery):
    battery_type: Literal['gauss_point_defense_1'] = 'gauss_point_defense_1'
    kind: ClassVar[PointDefenseKind] = 'gauss'
    rating: ClassVar[PointDefenseRating] = 1
    description = 'Point Defence Gauss Battery Type I'
    tl: int = 10
    base_tons = 20.0
    base_power = 5.0
    base_cost = 3_000_000.0


class GaussPointDefenseBattery2(_PointDefenseBattery):
    battery_type: Literal['gauss_point_defense_2'] = 'gauss_point_defense_2'
    kind: ClassVar[PointDefenseKind] = 'gauss'
    rating: ClassVar[PointDefenseRating] = 2
    description = 'Point Defence Gauss Battery Type II'
    tl: int = 12
    base_tons = 20.0
    base_power = 15.0
    base_cost = 6_000_000.0


class GaussPointDefenseBattery3(_PointDefenseBattery):
    battery_type: Literal['gauss_point_defense_3'] = 'gauss_point_defense_3'
    kind: ClassVar[PointDefenseKind] = 'gauss'
    rating: ClassVar[PointDefenseRating] = 3
    description = 'Point Defence Gauss Battery Type III'
    tl: int = 14
    base_tons = 20.0
    base_power = 25.0
    base_cost = 10_000_000.0


class TorpedoInterceptorCluster(ShipPart):
    battery_type: Literal['torpedo_interceptor_cluster'] = 'torpedo_interceptor_cluster'
    description: Literal['Torpedo-Interceptor Cluster'] = 'Torpedo-Interceptor Cluster'
    tl: int = 10
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info('One-shot system; must be replaced dockside after firing')
        notes.info('Four interceptors; each kills one missile on 6+ or torpedo on 8+')
        return notes

    @property
    def hardpoints_required(self) -> int:
        return 1

    @property
    def tons(self) -> float:
        return 1.0

    @property
    def cost(self) -> float:
        return 1_000_000.0

    @property
    def power(self) -> float:
        return 1.0


type PointDefenseBattery = Annotated[
    LaserPointDefenseBattery1
    | LaserPointDefenseBattery2
    | LaserPointDefenseBattery3
    | GaussPointDefenseBattery1
    | GaussPointDefenseBattery2
    | GaussPointDefenseBattery3
    | TorpedoInterceptorCluster,
    Field(discriminator='battery_type'),
]

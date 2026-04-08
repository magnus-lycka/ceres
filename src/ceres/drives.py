import math
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from .parts import ShipPart


class MDrive(ShipPart):
    rating: int
    armored: bool = False
    minimum_tl: ClassVar[int]
    tons_percent: ClassVar[float]

    def build_item(self) -> str | None:
        label = f'M-Drive {self.rating}'
        if self.armored:
            label += ' (Armored)'
        return label

    def _base_tons(self) -> float:
        return self.owner.displacement * self.tons_percent

    def compute_tons(self) -> float:
        tons = self._base_tons()
        if self.armored:
            tons *= 1.1
        return tons

    def compute_cost(self) -> float:
        cost = self._base_tons() * 2_000_000
        if self.armored:
            cost *= 1.01
        return cost

    def compute_power(self) -> float:
        return float(math.ceil(0.1 * self.owner.displacement * self.rating))


class MDrive0(MDrive):
    rating: Literal[0] = 0
    minimum_tl = 9
    tons_percent = 0.005


class MDrive1(MDrive):
    rating: Literal[1] = 1
    minimum_tl = 9
    tons_percent = 0.01


class MDrive2(MDrive):
    rating: Literal[2] = 2
    minimum_tl = 10
    tons_percent = 0.02


class MDrive3(MDrive):
    rating: Literal[3] = 3
    minimum_tl = 10
    tons_percent = 0.03


class MDrive4(MDrive):
    rating: Literal[4] = 4
    minimum_tl = 11
    tons_percent = 0.04


class MDrive5(MDrive):
    rating: Literal[5] = 5
    minimum_tl = 11
    tons_percent = 0.05


class MDrive6(MDrive):
    rating: Literal[6] = 6
    minimum_tl = 12
    tons_percent = 0.06


class MDrive7(MDrive):
    rating: Literal[7] = 7
    minimum_tl = 13
    tons_percent = 0.07


class MDrive8(MDrive):
    rating: Literal[8] = 8
    minimum_tl = 14
    tons_percent = 0.08


class MDrive9(MDrive):
    rating: Literal[9] = 9
    minimum_tl = 15
    tons_percent = 0.09


class MDrive10(MDrive):
    rating: Literal[10] = 10
    minimum_tl = 16
    tons_percent = 0.10


class MDrive11(MDrive):
    rating: Literal[11] = 11
    minimum_tl = 17
    tons_percent = 0.11


class JumpDrive(ShipPart):
    rating: int
    minimum_tl: ClassVar[int]
    tons_percent: ClassVar[float]

    def build_item(self) -> str | None:
        return f'Jump {self.rating}'

    def compute_tons(self) -> float:
        return self.owner.displacement * self.tons_percent + 5

    def compute_cost(self) -> float:
        return self.compute_tons() * 1_500_000

    def compute_power(self) -> float:
        return float(math.ceil(0.1 * self.owner.displacement * self.rating))


class JumpDrive1(JumpDrive):
    rating: Literal[1] = 1
    minimum_tl = 9
    tons_percent = 0.025


class JumpDrive2(JumpDrive):
    rating: Literal[2] = 2
    minimum_tl = 11
    tons_percent = 0.05


class JumpDrive3(JumpDrive):
    rating: Literal[3] = 3
    minimum_tl = 12
    tons_percent = 0.075


class JumpDrive4(JumpDrive):
    rating: Literal[4] = 4
    minimum_tl = 13
    tons_percent = 0.10


class JumpDrive5(JumpDrive):
    rating: Literal[5] = 5
    minimum_tl = 14
    tons_percent = 0.125


class JumpDrive6(JumpDrive):
    rating: Literal[6] = 6
    minimum_tl = 15
    tons_percent = 0.15


class JumpDrive7(JumpDrive):
    rating: Literal[7] = 7
    minimum_tl = 16
    tons_percent = 0.175


class JumpDrive8(JumpDrive):
    rating: Literal[8] = 8
    minimum_tl = 17
    tons_percent = 0.20


class JumpDrive9(JumpDrive):
    rating: Literal[9] = 9
    minimum_tl = 18
    tons_percent = 0.225


ShipMDrive = Annotated[
    MDrive0
    | MDrive1
    | MDrive2
    | MDrive3
    | MDrive4
    | MDrive5
    | MDrive6
    | MDrive7
    | MDrive8
    | MDrive9
    | MDrive10
    | MDrive11,
    Field(discriminator='rating'),
]

ShipJumpDrive = Annotated[
    JumpDrive1 | JumpDrive2 | JumpDrive3 | JumpDrive4 | JumpDrive5 | JumpDrive6 | JumpDrive7 | JumpDrive8 | JumpDrive9,
    Field(discriminator='rating'),
]


class DriveSection(ShipPart):
    m_drive: ShipMDrive | None = None
    jump_drive: ShipJumpDrive | None = None

    def _all_parts(self) -> list[ShipPart]:
        return [part for part in [self.m_drive, self.jump_drive] if part is not None]


class _FusionPlant(ShipPart):
    minimum_tl: ClassVar[int]
    power_per_ton: ClassVar[int]
    cost_per_ton: ClassVar[int]
    output: int

    def build_item(self) -> str | None:
        return f'Fusion (TL {self.minimum_tl})'

    @property
    def fusion_tl(self) -> int:
        return self.minimum_tl

    @property
    def effective_tl(self):
        return self.minimum_tl

    def compute_tons(self) -> float:
        return self.output / self.power_per_ton

    def compute_cost(self) -> float:
        return self.compute_tons() * self.cost_per_ton


class FusionPlantTL8(_FusionPlant):
    plant_type: Literal['fusion_tl8'] = 'fusion_tl8'
    minimum_tl = 8
    power_per_ton = 10
    cost_per_ton = 500_000


class FusionPlantTL12(_FusionPlant):
    plant_type: Literal['fusion_tl12'] = 'fusion_tl12'
    minimum_tl = 12
    power_per_ton = 15
    cost_per_ton = 1_000_000


class FusionPlantTL15(_FusionPlant):
    plant_type: Literal['fusion_tl15'] = 'fusion_tl15'
    minimum_tl = 15
    power_per_ton = 20
    cost_per_ton = 2_000_000

from typing import Annotated, ClassVar, Literal

from pydantic import Field

from .parts import CustomisableShipPart, EnergyInefficient, IncreasedSize, ShipPart, SizeReduction
from .spec import ShipSpec, SpecSection


class _PowerPlant(CustomisableShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    power_per_ton: ClassVar[int | float]
    cost_per_ton: ClassVar[int | float]
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            IncreasedSize.name,
            SizeReduction.name,
            EnergyInefficient.name,
        }
    )
    output: int

    def bulkhead_label(self) -> str:
        return 'Power Plant'

    @property
    def tons(self) -> float:
        tons = self.output / self.power_per_ton
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return tons * multiplier

    @property
    def cost(self) -> float:
        cost = (self.output / self.power_per_ton) * self.cost_per_ton
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return cost * multiplier

    @property
    def power(self) -> float:
        return 0.0

    def fuel_for_weeks(self, weeks: int) -> float:
        """Fuel in tons needed for the given number of weeks of operation."""
        return 0.10 * self.tons * weeks / 4

    @property
    def fuel_period_weeks(self) -> int:
        """Baseline fuel period length in weeks (used by OperationFuel rounding)."""
        return 4


class _FusionPlant(_PowerPlant):
    def build_item(self) -> str | None:
        return f'Fusion (TL {self.tl}), Power {self.output}'

    @property
    def fusion_tl(self) -> int:
        return self.tl


class FusionPlantTL8(_FusionPlant):
    plant_type: Literal['fusion_tl8'] = 'fusion_tl8'
    tl: int = 8
    power_per_ton: ClassVar[int] = 10
    cost_per_ton: ClassVar[int] = 500_000


class FusionPlantTL12(_FusionPlant):
    plant_type: Literal['fusion_tl12'] = 'fusion_tl12'
    tl: int = 12
    power_per_ton: ClassVar[int] = 15
    cost_per_ton: ClassVar[int] = 1_000_000


class FusionPlantTL15(_FusionPlant):
    plant_type: Literal['fusion_tl15'] = 'fusion_tl15'
    tl: int = 15
    power_per_ton: ClassVar[int] = 20
    cost_per_ton: ClassVar[int] = 2_000_000


class FissionPlant(_PowerPlant):
    plant_type: Literal['fission'] = 'fission'
    tl: int = 6
    power_per_ton: ClassVar[int] = 8
    cost_per_ton: ClassVar[int] = 400_000

    def build_item(self) -> str | None:
        return f'Fission Plant (TL {self.tl}), Power {self.output}'


class ChemicalPlant(_PowerPlant):
    plant_type: Literal['chemical'] = 'chemical'
    tl: int = 7
    power_per_ton: ClassVar[int] = 5
    cost_per_ton: ClassVar[int] = 250_000

    def build_item(self) -> str | None:
        return f'Chemical Plant (TL {self.tl}), Power {self.output}'

    def fuel_for_weeks(self, weeks: int) -> float:
        """Chemical plants need 10 tons of fuel per ton of plant per 2 weeks."""
        return 10.0 * self.tons * weeks / 2

    @property
    def fuel_period_weeks(self) -> int:
        return 2


type AnyPowerPlant = Annotated[
    FusionPlantTL8 | FusionPlantTL12 | FusionPlantTL15 | FissionPlant | ChemicalPlant,
    Field(discriminator='plant_type'),
]


class EmergencyPowerSystem(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    @classmethod
    def from_fusion_plant(cls, plant: _FusionPlant) -> EmergencyPowerSystem:
        return cls()

    def build_item(self) -> str | None:
        return 'Emergency Power System'

    @property
    def source_plant(self) -> _PowerPlant:
        power_section = getattr(self.assembly, 'power', None)
        plant = None if power_section is None else power_section.plant
        if plant is None:
            raise RuntimeError('EmergencyPowerSystem requires a power plant')
        return plant

    @property
    def tons(self) -> float:
        return self.source_plant.tons * 0.1

    @property
    def cost(self) -> float:
        return self.source_plant.cost * 0.1

    @property
    def power(self) -> float:
        return 0.0


class PowerSection(ShipPart):
    plant: AnyPowerPlant | None = None
    emergency_power_system: EmergencyPowerSystem | None = None

    def validate_emergency_power_system(self) -> None:
        if self.emergency_power_system is not None and self.plant is None:
            raise RuntimeError('EmergencyPowerSystem requires a power plant')

    def _all_parts(self) -> list[ShipPart]:
        return [part for part in [self.plant, self.emergency_power_system] if part is not None]

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.plant is not None:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.POWER,
                    self.plant,
                    power=float(self.plant.output),
                    emphasize_power=True,
                )
            )
        if self.emergency_power_system is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.POWER, self.emergency_power_system))

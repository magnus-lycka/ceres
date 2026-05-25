from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import NoteList

from ..parts import Modification, ShipPart

SpinExtPlasmaDriveEnergyEfficient = Modification(
    name='Energy Efficient',
    power_multiplier=0.80,
    info_notes=('Energy Efficient: consumes 20% less Power',),
)
SpinExtPlasmaDriveFuelEfficient = Modification(
    name='Fuel Efficient',
    fuel_delta_percent=-0.20,
    info_notes=('Fuel Efficient: consumes 20% less fuel',),
)
SpinExtPlasmaDriveSizeReduction = Modification(
    name='Size Reduction',
    tons_delta_percent=-0.10,
    info_notes=('Size Reduction: uses 10% less tonnage',),
)
SpinExtPlasmaDriveEnergyInefficient = Modification(
    name='Energy Inefficient',
    power_multiplier=1.30,
    info_notes=('Energy Inefficient: consumes 30% more Power',),
)
SpinExtPlasmaDriveIncreasedSize = Modification(
    name='Increased Size',
    tons_delta_percent=0.25,
    info_notes=('Increased Size: uses 25% more tonnage',),
)
SpinExtPlasmaDriveFuelInefficient = Modification(
    name='Fuel Inefficient',
    fuel_delta_percent=0.25,
    info_notes=('Fuel Inefficient: consumes 25% more fuel',),
)


class SpinExtPlasmaDrive(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    drive_type: Literal['spinext_plasma_drive'] = 'spinext_plasma_drive'
    description: Literal['SpinExt Plasma Drive'] = 'SpinExt Plasma Drive'
    tl: int = 8
    thrust: float = Field(gt=0)
    modifications: list[Modification] = Field(default_factory=list)
    tons_percent_per_thrust: ClassVar[float] = 0.20
    cost_per_ton: ClassVar[int] = 400_000
    power_per_ton: ClassVar[int] = 1
    fuel_percent_per_thrust_hour: ClassVar[float] = 0.01

    @property
    def tons_multiplier(self) -> float:
        return 1.0 + sum(modification.tons_delta_percent for modification in self.modifications)

    @property
    def power_multiplier(self) -> float:
        result = 1.0
        for modification in self.modifications:
            result *= modification.power_multiplier
        return result

    @property
    def fuel_multiplier(self) -> float:
        return 1.0 + sum(modification.fuel_delta_percent for modification in self.modifications)

    @property
    def tons(self) -> float:
        return self.assembly.displacement * self.tons_percent_per_thrust * self.thrust * self.tons_multiplier

    @property
    def cost(self) -> float:
        return self.tons * self.cost_per_ton

    @property
    def power(self) -> float:
        return self.tons * self.power_per_ton * self.power_multiplier

    @property
    def fuel_tons_per_hour(self) -> float:
        return self.assembly.displacement * self.fuel_percent_per_thrust_hour * self.thrust * self.fuel_multiplier

    def item_description(self) -> str:
        description = f'SpinExt Plasma Drive, Thrust {self.thrust:g}'
        if self.modifications:
            return f'{description} ({", ".join(modification.name for modification in self.modifications)})'
        return description

    def build_notes(self) -> list:
        notes = NoteList()
        notes.info('Uses standard liquid hydrogen fuel')
        notes.info(f'Consumes {self.fuel_tons_per_hour:g} tons of fuel per hour')
        notes.info('Does not require or benefit from a gravity field, so it works in deep space')
        for modification in self.modifications:
            notes += modification.notes
        return notes


type AnyPlasmaDrive = Annotated[SpinExtPlasmaDrive, Field(discriminator='drive_type')]

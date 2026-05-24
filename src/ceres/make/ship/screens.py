from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import CeresModel, NoteList

from .parts import CustomisableShipPart, EnergyEfficient, ShipPart, SizeReduction
from .spec import ShipSpec, SpecSection


class _Screen(CustomisableShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    screen_type: str
    description: ClassVar[str]
    damage_reduction: ClassVar[str]
    base_tons: ClassVar[float]
    base_cost: ClassVar[float]
    base_power: ClassVar[float]
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            EnergyEfficient.name,
            SizeReduction.name,
        }
    )

    @property
    def tons(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return self.base_tons * multiplier

    @property
    def cost(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return self.base_cost * multiplier

    @property
    def power(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return self.base_power * multiplier


class MesonScreen(_Screen):
    screen_type: Literal['meson_screen'] = 'meson_screen'
    description = 'Meson Screen'
    damage_reduction = '2D × 10'
    tl: int = 13
    base_tons = 10.0
    base_cost = 20_000_000.0
    base_power = 30.0


class NuclearDamper(_Screen):
    screen_type: Literal['nuclear_damper'] = 'nuclear_damper'
    description = 'Nuclear Damper'
    damage_reduction = '2D'
    tl: int = 12
    base_tons = 10.0
    base_cost = 10_000_000.0
    base_power = 20.0


class DeflectorScreen(_Screen):
    screen_type: Literal['deflector_screen'] = 'deflector_screen'
    description = 'Deflector Screen'
    damage_reduction = '1D'
    tl: int = 10
    base_tons = 5.0
    base_cost = 5_000_000.0
    base_power = 10.0


class EnergyShield(_Screen):
    screen_type: Literal['energy_shield'] = 'energy_shield'
    description = 'Energy Shield'
    damage_reduction = 'Energy buffer 10'
    tl: int = 14
    base_tons = 20.0
    base_cost = 25_000_000.0
    base_power = 50.0


class ImprovedEnergyShield(_Screen):
    screen_type: Literal['improved_energy_shield'] = 'improved_energy_shield'
    description = 'Improved Energy Shield'
    damage_reduction = 'Energy buffer 20'
    tl: int = 16
    base_tons = 15.0
    base_cost = 35_000_000.0
    base_power = 75.0


class AdvancedEnergyShield(_Screen):
    screen_type: Literal['advanced_energy_shield'] = 'advanced_energy_shield'
    description = 'Advanced Energy Shield'
    damage_reduction = 'Energy buffer 50'
    tl: int = 18
    base_tons = 10.0
    base_cost = 60_000_000.0
    base_power = 100.0


class BlackGlobeGenerator(_Screen):
    screen_type: Literal['black_globe_generator'] = 'black_globe_generator'
    description = 'Black Globe Generator'
    damage_reduction = 'Absorbs attacks into capacitors'
    tl: int = 15
    base_tons = 50.0
    base_cost = 100_000_000.0
    base_power = 30.0

    def build_notes(self):
        notes = NoteList(super().build_notes())
        notes.info('Not commercially available; availability is at Referee discretion')
        notes.info('Active globe prevents manoeuvre, dodging, jumping, weapons, and sensors')
        notes.info('Absorbed attacks require capacitor capacity; overload destroys the ship')
        notes.info(
            'Flicker, capacitor discharge, and overload are operational combat rules not modelled in build specs'
        )
        return notes


class BlackGlobeCapacitorBank(ShipPart):
    description: Literal['Black Globe Capacitor Bank'] = 'Black Globe Capacitor Bank'
    tl: int = 15
    tons: float
    power: float = 0.0
    cost: ClassVar[float]

    @property
    def cost(self) -> float:
        return self.tons * 3_000_000.0

    @property
    def damage_capacity(self) -> float:
        return self.tons * 50.0

    def build_notes(self):
        notes = NoteList(super().build_notes())
        notes.info(f'Absorbs {self.damage_capacity:g} points of damage for black globe generators')
        return notes


type Screen = Annotated[
    MesonScreen
    | NuclearDamper
    | DeflectorScreen
    | EnergyShield
    | ImprovedEnergyShield
    | AdvancedEnergyShield
    | BlackGlobeGenerator,
    Field(discriminator='screen_type'),
]


class ScreensSection(CeresModel):
    screens: list[Screen] = Field(default_factory=list)
    capacitor_banks: list[BlackGlobeCapacitorBank] = Field(default_factory=list)

    def _all_parts(self) -> list[ShipPart]:
        return [*self.screens, *self.capacitor_banks]

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for row in ship._grouped_spec_rows(SpecSection.SCREENS, self._all_parts()):
            spec.add_row(row)

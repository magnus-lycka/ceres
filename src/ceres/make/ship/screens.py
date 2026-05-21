from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import CeresModel

from .parts import CustomisableShipPart, EnergyEfficient, SizeReduction
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
    damage_reduction = 'Radiation and particle damage'
    tl: int = 10
    base_tons = 5.0
    base_cost = 5_000_000.0
    base_power = 10.0


class EnergyShield(_Screen):
    screen_type: Literal['energy_shield'] = 'energy_shield'
    description = 'Energy Shield'
    damage_reduction = 'Energy weapon damage'
    tl: int = 14
    base_tons = 50.0
    base_cost = 60_000_000.0
    base_power = 90.0


type Screen = Annotated[
    MesonScreen | NuclearDamper | DeflectorScreen | EnergyShield,
    Field(discriminator='screen_type'),
]


class ScreensSection(CeresModel):
    screens: list[Screen] = Field(default_factory=list)

    def _all_parts(self) -> list[_Screen]:
        return list(self.screens)

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for row in ship._grouped_spec_rows(SpecSection.SCREENS, self.screens):
            spec.add_row(row)

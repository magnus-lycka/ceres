from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import NoteList

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


class _SterlingFissionPlant(_PowerPlant):
    minimum_tons: ClassVar[int] = 2
    lifespan_years: ClassVar[int]

    def build_item(self) -> str | None:
        return f'Sterling Fission (TL {self.tl}), Power {self.output}'

    def _base_tons(self) -> float:
        return max(self.minimum_tons, self.output / self.power_per_ton)

    @property
    def tons(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return self._base_tons() * multiplier

    @property
    def cost(self) -> float:
        cost = self._base_tons() * self.cost_per_ton
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return cost * multiplier

    def fuel_for_weeks(self, weeks: int) -> float:
        return 0.0

    def power_per_ton_at_age(self, age_years: int) -> float:
        years_beyond_lifespan = max(0, age_years - self.lifespan_years)
        return max(0, self.power_per_ton - years_beyond_lifespan)

    def output_at_age(self, age_years: int) -> float:
        return self.tons * self.power_per_ton_at_age(age_years)

    def build_notes(self) -> list:
        notes = NoteList()
        drives = getattr(self.assembly, 'drives', None) if self._assembly is not None else None
        if drives is not None and drives.j_drive is not None:
            notes.warning('Sterling fission power plants cannot directly operate jump drives')
            notes.info('Sterling fission power plants may charge batteries for jump drive use')
        return notes


class SterlingFissionPlantTL6(_SterlingFissionPlant):
    plant_type: Literal['sterling_fission_tl6'] = 'sterling_fission_tl6'
    tl: int = 6
    power_per_ton: ClassVar[int] = 3
    cost_per_ton: ClassVar[int] = 400_000
    lifespan_years: ClassVar[int] = 10


class SterlingFissionPlant(_SterlingFissionPlant):
    plant_type: Literal['sterling_fission'] = 'sterling_fission'
    tl: int = 8
    power_per_ton: ClassVar[int] = 4
    cost_per_ton: ClassVar[int] = 600_000
    lifespan_years: ClassVar[int] = 15


class SterlingFissionPlantTL12(_SterlingFissionPlant):
    plant_type: Literal['sterling_fission_tl12'] = 'sterling_fission_tl12'
    tl: int = 12
    power_per_ton: ClassVar[int] = 6
    cost_per_ton: ClassVar[int] = 800_000
    lifespan_years: ClassVar[int] = 20


class AntimatterPlant(_PowerPlant):
    plant_type: Literal['antimatter'] = 'antimatter'
    tl: int = 20
    power_per_ton: ClassVar[int] = 100
    cost_per_ton: ClassVar[int] = 10_000_000

    def build_item(self) -> str | None:
        return f'Antimatter Plant (TL {self.tl}), Power {self.output}'


type AnyPowerPlant = Annotated[
    FusionPlantTL8
    | FusionPlantTL12
    | FusionPlantTL15
    | FissionPlant
    | ChemicalPlant
    | SterlingFissionPlantTL6
    | SterlingFissionPlant
    | SterlingFissionPlantTL12
    | AntimatterPlant,
    Field(discriminator='plant_type'),
]


class _SolarPowerSource(ShipPart):
    cost: ClassVar[float]
    power: ClassVar[float]
    solar_type: str
    tl: int
    grade: ClassVar[str]
    power_per_unit: ClassVar[int | float]
    cost_per_unit: ClassVar[int | float]
    units: float

    @property
    def cost(self) -> float:
        return self.units * self.cost_per_unit

    @property
    def power(self) -> float:
        return 0.0

    @property
    def output(self) -> float:
        return self.units * self.power_per_unit

    def _output_label(self) -> str:
        return f'{self.output:g}'


class _SolarPanels(ShipPart):
    cost: ClassVar[float]
    power: ClassVar[float]
    solar_type: str
    tl: int
    tons: float = Field(0.5, ge=0.5)
    power_per_ton: ClassVar[int]
    cost_per_ton: ClassVar[int]

    def build_item(self) -> str | None:
        return f'Solar Panels (TL {self.tl}), Power {self.output:g}'

    @property
    def cost(self) -> float:
        return self.tons * self.cost_per_ton

    @property
    def power(self) -> float:
        return 0.0

    @property
    def output(self) -> float:
        return self.tons * self.power_per_ton

    def build_notes(self) -> list:
        notes = NoteList()
        notes.info('Solar panel Power assumes operation in a star habitable zone')
        notes.info('Solar panels are useless in interstellar space')
        notes.info('Solar panels require 1D rounds to deploy or retract')
        notes.info('Ships cannot jump with solar panels deployed')
        notes.info('Ships cannot manoeuvre above Thrust 1 with solar panels deployed')
        notes.info('Solar panels can charge batteries')
        return notes


class SolarPanelsTL6(_SolarPanels):
    solar_type: Literal['solar_panels_tl6'] = 'solar_panels_tl6'
    tl: int = 6
    power_per_ton: ClassVar[int] = 1
    cost_per_ton: ClassVar[int] = 100_000


class SolarPanelsTL8(_SolarPanels):
    solar_type: Literal['solar_panels_tl8'] = 'solar_panels_tl8'
    tl: int = 8
    power_per_ton: ClassVar[int] = 2
    cost_per_ton: ClassVar[int] = 200_000


class SolarPanelsTL12(_SolarPanels):
    solar_type: Literal['solar_panels_tl12'] = 'solar_panels_tl12'
    tl: int = 12
    power_per_ton: ClassVar[int] = 3
    cost_per_ton: ClassVar[int] = 400_000


class _SolarCoating(_SolarPowerSource):
    tons: ClassVar[float]

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def output(self) -> float:
        output = super().output
        if self._is_close_or_dispersed_hull():
            output *= 0.5
        return output

    def build_item(self) -> str | None:
        return f'Solar Coating ({self.grade}), Power {self._output_label()}'

    def build_notes(self) -> list:
        notes = NoteList()
        if self._assembly is not None:
            maximum_units = self.assembly.displacement * 0.4
            if self.units > maximum_units:
                notes.error(f'Solar coating exceeds 40% hull coverage: {self.units:g} > {maximum_units:g}')
            description = self._hull_description()
            if 'streamlined' in description:
                notes.error('Solar coating cannot be applied to streamlined hulls')
        notes.info('DM+1 to detect the ship while solar coating is in use')
        return notes

    def _is_close_or_dispersed_hull(self) -> bool:
        if self._assembly is None:
            return False
        description = self._hull_description()
        return 'close structure' in description or 'dispersed structure' in description

    def _hull_description(self) -> str:
        hull = getattr(self.assembly, 'hull', None)
        if hull is None:
            return ''
        return hull.configuration.description.lower()


class EnhancedSolarCoating(_SolarCoating):
    solar_type: Literal['enhanced_solar_coating'] = 'enhanced_solar_coating'
    tl: int = 10
    grade: ClassVar[str] = 'Enhanced'
    power_per_unit: ClassVar[float] = 0.1
    cost_per_unit: ClassVar[int] = 300_000


class AdvancedSolarCoating(_SolarCoating):
    solar_type: Literal['advanced_solar_coating'] = 'advanced_solar_coating'
    tl: int = 12
    grade: ClassVar[str] = 'Advanced'
    power_per_unit: ClassVar[float] = 0.2
    cost_per_unit: ClassVar[int] = 400_000


type AnySolarPowerSource = Annotated[
    SolarPanelsTL6 | SolarPanelsTL8 | SolarPanelsTL12 | EnhancedSolarCoating | AdvancedSolarCoating,
    Field(discriminator='solar_type'),
]


class _HighEfficiencyBatteries(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    battery_type: str
    tl: int
    stored_power: int
    power_per_ton: ClassVar[int]
    cost_per_ton: ClassVar[int]

    @property
    def tons(self) -> float:
        return self.stored_power / self.power_per_ton

    @property
    def cost(self) -> float:
        return self.tons * self.cost_per_ton

    @property
    def power(self) -> float:
        return 0.0

    def build_item(self) -> str | None:
        return f'High-Efficiency Batteries (TL {self.tl}), Power {self.stored_power:g}'

    def build_notes(self) -> list:
        notes = NoteList()
        notes.info('Batteries store power for later use; they do not generate continuous power')
        return notes


class HighEfficiencyBatteriesTL10(_HighEfficiencyBatteries):
    battery_type: Literal['high_efficiency_batteries_tl10'] = 'high_efficiency_batteries_tl10'
    tl: int = 10
    power_per_ton: ClassVar[int] = 40
    cost_per_ton: ClassVar[int] = 100_000


class HighEfficiencyBatteriesTL12(_HighEfficiencyBatteries):
    battery_type: Literal['high_efficiency_batteries_tl12'] = 'high_efficiency_batteries_tl12'
    tl: int = 12
    power_per_ton: ClassVar[int] = 60
    cost_per_ton: ClassVar[int] = 200_000


type AnyHighEfficiencyBatteries = Annotated[
    HighEfficiencyBatteriesTL10 | HighEfficiencyBatteriesTL12,
    Field(discriminator='battery_type'),
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
    solar: list[AnySolarPowerSource] = Field(default_factory=list)
    batteries: list[AnyHighEfficiencyBatteries] = Field(default_factory=list)
    emergency_power_system: EmergencyPowerSystem | None = None

    def validate_emergency_power_system(self) -> None:
        if self.emergency_power_system is not None and self.plant is None:
            raise RuntimeError('EmergencyPowerSystem requires a power plant')

    def _all_parts(self) -> list[ShipPart]:
        return [
            part for part in [self.plant, *self.solar, *self.batteries, self.emergency_power_system] if part is not None
        ]

    @property
    def output(self) -> float:
        plant_output = 0.0 if self.plant is None else float(self.plant.output)
        solar_output = sum(source.output for source in self.solar)
        return plant_output + solar_output

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
        for source in self.solar:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.POWER,
                    source,
                    power=source.output,
                    emphasize_power=True,
                )
            )
        for battery in self.batteries:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.POWER,
                    battery,
                    power=battery.stored_power,
                )
            )
        if self.emergency_power_system is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.POWER, self.emergency_power_system))

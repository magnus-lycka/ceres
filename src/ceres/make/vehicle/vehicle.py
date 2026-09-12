"""The vehicle design object.

A vehicle is built from a type and a number of Spaces. Everything the design
states about itself is derived from those two, the Tech Level, and what gets
installed later.

Rules: refs/vehicle/03_vehicle_design.md, refs/vehicle/02_new_rules.md
"""

from math import ceil
from typing import Any

from pydantic import Field, field_validator

from ceres.shared import Assembly

from .armour import Armour, Face
from .comfort import comfort_label
from .customisations import CustomisationUnion
from .features import Feature
from .options import Autopilot, NavigationSystem, OptionUnion, SensorSystem, VehicleComputer
from .size import VehicleSize, target_size_dm
from .spec import VehicleSpec
from .speed import SpeedBand
from .traits import Trait
from .types import VehicleType

_HULL_PER_STRUCTURE = 10

# refs/vehicle/02_new_rules.md — cruising increases Range by 50%.
_CRUISE_RANGE_BONUS = 1.5

# refs/vehicle/03_vehicle_design.md — a Space of cargo is a quarter of a dTon.
_TONS_PER_CARGO_SPACE = 0.25


class Vehicle(Assembly):
    """A vehicle design.

    Hull and Structure are both kept: modifiers apply to Hull, and Structure —
    what the stat block prints and play uses — is a tenth of the result,
    rounded up once at the end (RIV-001).
    """

    name: str
    vehicle_type: VehicleType
    spaces: int
    tl: int
    features: list[Feature] = Field(default_factory=list)
    customisations: list[CustomisationUnion] = Field(default_factory=list)
    options: list[OptionUnion] = Field(default_factory=list)
    crew: int = 0
    passengers: int = 0
    cargo_spaces: int = 0

    @field_validator('spaces')
    @classmethod
    def _sizeable(cls, spaces: int) -> int:
        # Too few Spaces is not a rule violation to note but an incoherent
        # design: there is no vehicle to size, cost or damage. VehicleSize owns
        # what a workable Spaces count is, so ask it rather than repeat it.
        VehicleSize.for_spaces(spaces)
        return spaces

    def model_post_init(self, __context: Any) -> None:
        if self.tl < self.vehicle_type.tl:
            self.error(f'{self.vehicle_type.value} requires TL{self.vehicle_type.tl}, this design is TL{self.tl}')
        self._check_features()
        self._check_it_fits()

    def _check_it_fits(self) -> None:
        if (over := -self.available_spaces) > 0:
            self.error(
                f'this design needs {over} more Space(s) than its {self.spaces} provide, '
                f'once everything installed and carried is accounted for'
            )

    def _check_features(self) -> None:
        for feature in self.features:
            if not feature.allowed_on(self.vehicle_type):
                self.error(f'{self.vehicle_type.value} cannot take the {feature.value} feature')
            if self.tl < feature.tl:
                self.error(f'the {feature.value} feature requires TL{feature.tl}, this design is TL{self.tl}')
        for index, feature in enumerate(self.features):
            for other in self.features[index + 1 :]:
                if feature.conflicts_with(other):
                    self.error(f'the {feature.value} and {other.value} features are not compatible')

    @property
    def size(self) -> VehicleSize:
        return VehicleSize.for_spaces(self.spaces)

    @property
    def hull(self) -> float:
        """Spaces times the type's rate. Never less than 1, whatever reduces it.

        Not rounded: the rules round once, at Structure (RIV-001). A type such as
        an airship at 0.2 per Space produces a genuinely fractional Hull.
        """
        return max(self.spaces * self.vehicle_type.hull_per_space, 1)

    @property
    def structure(self) -> int:
        """The damage threshold: one-tenth of Hull, rounded up."""
        return ceil(self.hull / _HULL_PER_STRUCTURE)

    @property
    def shipping_tons(self) -> float:
        """Shipping tonnage: what this occupies as cargo, or in a hangar."""
        return self.spaces * self.vehicle_type.shipping_per_space

    @property
    def base_cost(self) -> float:
        """Spaces times the type's rate, before features."""
        return self.spaces * self.vehicle_type.cost_per_space

    @property
    def cost(self) -> float:
        """Base Cost plus each feature's and customisation's share of it.

        Percentages are added against the base rather than compounding, as
        refs/vehicle/05_features.md states under Multiple Features, and
        refs/vehicle/06_customisation.md is explicit that a customisation's
        addition is computed from the initial base Cost and not from the base as
        already modified by features. Costs that are not fractions of the base,
        such as a power plant's, are added on top.
        """
        fractions = sum(feature.added_cost for feature in self.features) + sum(
            customisation.added_cost for customisation in self.customisations
        )
        absolute = sum(customisation.cost(self.spaces) for customisation in self.customisations) + sum(
            self._option_cost(option) for option in self.options
        )
        return self.base_cost * (1 + fractions) + absolute

    def _option_cost(self, option) -> float:
        """What an option costs this design.

        A computer becomes standard equipment at no Cost once the vehicle is
        advanced enough, which only the vehicle knows.
        """
        if isinstance(option, VehicleComputer):
            return option.cost_at_tl(self.tl)
        return option.cost(self.spaces)

    @property
    def available_spaces(self) -> int:
        """Spaces still unspent, after everything installed and carried."""
        taken = sum(option.spaces(self.spaces) for option in self.options)
        customised = sum(c.spaces_delta(self.spaces) for c in self.customisations)
        return self.spaces + customised - taken - self.occupant_spaces - self.cargo_spaces

    @property
    def occupants(self) -> int:
        return self.crew + self.passengers

    @property
    def occupant_spaces(self) -> int:
        """One Space each, for a vehicle built to human dimensions."""
        return self.occupants

    @property
    def cargo_tons(self) -> float:
        """A Space of cargo is a quarter of a displacement ton, about 250kg."""
        return self.cargo_spaces * _TONS_PER_CARGO_SPACE

    @property
    def comfort_points(self) -> float:
        """Each standard seat Space is worth one, plus what the fittings carry."""
        from_fittings = sum(getattr(option, 'comfort_points', 0.0) for option in self.options)
        return self.occupant_spaces + from_fittings

    @property
    def comfort_level(self) -> float | None:
        """Comfort Points shared between the occupants, or None with nobody aboard."""
        if self.occupants == 0:
            return None
        return self.comfort_points / self.occupants

    @property
    def comfort_label(self) -> str | None:
        level = self.comfort_level
        return None if level is None else comfort_label(level)

    @property
    def agility(self) -> int:
        """Type, size, features and the control system (RIV-007)."""
        return (
            self.vehicle_type.agility
            + self.size.agility_modifier
            + sum(feature.agility for feature in self.features)
            + sum(option.agility for option in self.options)
        )

    def _first_option(self, option_cls: type):
        return next((option for option in self.options if isinstance(option, option_cls)), None)

    @property
    def autopilot_skill(self) -> int | None:
        """The skill level the vehicle can pilot itself at, if it can."""
        autopilot = self._first_option(Autopilot)
        return None if autopilot is None else autopilot.skill_level

    @property
    def navigation_dm(self) -> int | None:
        navigation = self._first_option(NavigationSystem)
        return None if navigation is None else navigation.navigation_dm

    @property
    def sensors_dm(self) -> int | None:
        sensors = self._first_option(SensorSystem)
        return None if sensors is None else sensors.sensors_dm

    @property
    def sensors_range_km(self) -> int | None:
        sensors = self._first_option(SensorSystem)
        return None if sensors is None else sensors.range_km

    @property
    def speed(self) -> SpeedBand:
        """Maximum Speed Band: the type's at this Tech Level, less the size penalty."""
        bands = (
            self.size.speed_band_modifier
            + sum(feature.speed_bands for feature in self.features)
            + sum(customisation.speed_bands for customisation in self.customisations)
        )
        return self.vehicle_type.speed_at(self.tl).shifted(bands)

    @property
    def cruise_speed(self) -> SpeedBand:
        return self.speed.cruise

    @property
    def range_km(self) -> int | None:
        """Range in kilometres, or None where the type states none at this TL."""
        stated = self.vehicle_type.range_at(self.tl)
        if stated is None:
            return None
        distance = float(stated)
        for feature in self.features:
            distance *= feature.range_multiplier
        for customisation in self.customisations:
            distance *= customisation.range_multiplier
        # Fuel percentages are pooled and applied to the Range already adjusted
        # by features and power plants, as the Range Modifications section says.
        fuel = sum(customisation.range_fraction for customisation in self.customisations)
        return round(distance * (1 + fuel))

    @property
    def armour(self) -> Armour:
        """Protection on each face. Nothing buys armour yet, so this is the
        Base Protection the Tech Level provides."""
        return Armour.unarmoured(self.tl)

    @property
    def target_size_dm(self) -> int:
        """How much easier this vehicle is to hit for being the size it is."""
        return target_size_dm(self.spaces)

    @property
    def cruise_range_km(self) -> int | None:
        """Range while cruising, which the rules put at half again."""
        if self.range_km is None:
            return None
        return round(self.range_km * _CRUISE_RANGE_BONUS)

    @property
    def features_and_traits(self) -> list[str]:
        """What the catalogue prints on one line, features and traits together."""
        return sorted({feature.value for feature in self.features} | {trait.value for trait in self.traits})

    def build_spec(self) -> VehicleSpec:
        return VehicleSpec(
            name=self.name,
            vehicle_type=self.vehicle_type,
            size=self.size,
            spaces=self.spaces,
            target_size_dm=self.target_size_dm,
            features_and_traits=self.features_and_traits,
            tl=self.tl,
            skill=self.vehicle_type.skill,
            agility=self.agility,
            speed=self.speed,
            cruise_speed=self.cruise_speed,
            range_km=self.range_km,
            cruise_range_km=self.cruise_range_km,
            crew=self.crew,
            passengers=self.passengers,
            comfort_label=self.comfort_label,
            cargo_tons=self.cargo_tons,
            structure=self.structure,
            shipping_tons=self.shipping_tons,
            cost=self.cost,
            armour={face: self.armour.protection(face) for face in Face},
            notes=self.notes,
        )

    @property
    def traits(self) -> tuple[Trait, ...]:
        from_features = tuple(trait for feature in self.features for trait in feature.traits)
        return self.vehicle_type.traits + self.size.traits + from_features

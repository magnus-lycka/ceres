from enum import StrEnum
from typing import Any, ClassVar

from pydantic import PrivateAttr

from .base import CeresModel, Note, NoteCategory, ShipBase


class CustomisationGrade(StrEnum):
    EARLY_PROTOTYPE = 'EARLY_PROTOTYPE'
    PROTOTYPE = 'PROTOTYPE'
    BUDGET = 'BUDGET'
    ADVANCED = 'ADVANCED'
    VERY_ADVANCED = 'VERY_ADVANCED'
    HIGH_TECHNOLOGY = 'HIGH_TECHNOLOGY'

    @property
    def display_name(self) -> str:
        return self.value.replace('_', ' ').title()

    @property
    def required_advantages(self) -> int:
        return {
            CustomisationGrade.EARLY_PROTOTYPE: 0,
            CustomisationGrade.PROTOTYPE: 0,
            CustomisationGrade.BUDGET: 0,
            CustomisationGrade.ADVANCED: 1,
            CustomisationGrade.VERY_ADVANCED: 2,
            CustomisationGrade.HIGH_TECHNOLOGY: 3,
        }[self]

    @property
    def required_disadvantages(self) -> int:
        return {
            CustomisationGrade.EARLY_PROTOTYPE: 2,
            CustomisationGrade.PROTOTYPE: 1,
            CustomisationGrade.BUDGET: 1,
            CustomisationGrade.ADVANCED: 0,
            CustomisationGrade.VERY_ADVANCED: 0,
            CustomisationGrade.HIGH_TECHNOLOGY: 0,
        }[self]

    @property
    def base_cost_multiplier(self) -> float:
        return {
            CustomisationGrade.EARLY_PROTOTYPE: 11.0,
            CustomisationGrade.PROTOTYPE: 6.0,
            CustomisationGrade.BUDGET: 0.75,
            CustomisationGrade.ADVANCED: 1.10,
            CustomisationGrade.VERY_ADVANCED: 1.25,
            CustomisationGrade.HIGH_TECHNOLOGY: 1.50,
        }[self]

    @property
    def base_tons_multiplier(self) -> float:
        return {
            CustomisationGrade.EARLY_PROTOTYPE: 2.0,
            CustomisationGrade.PROTOTYPE: 1.0,
            CustomisationGrade.BUDGET: 1.0,
            CustomisationGrade.ADVANCED: 1.0,
            CustomisationGrade.VERY_ADVANCED: 1.0,
            CustomisationGrade.HIGH_TECHNOLOGY: 1.0,
        }[self]

    @property
    def tl_delta(self) -> int:
        return {
            CustomisationGrade.EARLY_PROTOTYPE: -2,
            CustomisationGrade.PROTOTYPE: -1,
            CustomisationGrade.BUDGET: 0,
            CustomisationGrade.ADVANCED: 1,
            CustomisationGrade.VERY_ADVANCED: 2,
            CustomisationGrade.HIGH_TECHNOLOGY: 3,
        }[self]


class Customisation(CeresModel):
    name: str
    advantage: int = 0
    disadvantage: int = 0
    cost_multiplier: float = 1.0
    tons_delta_percent: float = 0.0
    power_multiplier: float = 1.0
    fuel_multiplier: float = 1.0
    tl_delta: int = 0
    info_notes: tuple[str, ...] = ()
    model_config = {'frozen': True}

    def build_item(self) -> str | None:
        return self.name

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message=message) for message in self.info_notes]


SizeReduction = Customisation(name='Size Reduction', advantage=1, tons_delta_percent=-0.10)
IncreasedSize = Customisation(name='Increased Size', disadvantage=1, tons_delta_percent=0.25)
EnergyEfficient = Customisation(name='Energy Efficient', advantage=1, power_multiplier=0.75)
EnergyInefficient = Customisation(name='Energy Inefficient', disadvantage=1, power_multiplier=1.25)
LongRange = Customisation(
    name='Long Range',
    advantage=2,
    info_notes=('Range increased by one band, to a maximum of Very Long',),
)
OrbitalRange = Customisation(
    name='Orbital Range',
    advantage=1,
    info_notes=('Operational range increased to orbital distances',),
)
VeryHighYield = Customisation(name='Very High Yield', advantage=2)


class ShipPart(CeresModel):
    cost: float = 0.0
    power: float = 0.0
    tons: float = 0.0
    armoured_bulkhead: bool = False
    minimum_tl: ClassVar[int] = 0
    _ship: ShipBase | None = PrivateAttr(default=None)
    _armoured_bulkhead_part: ShipPart | None = PrivateAttr(default=None)
    model_config = {'frozen': True}

    def build_notes(self) -> list[Note]:
        if self.armoured_bulkhead:
            return [Note(category=NoteCategory.INFO, message='Armoured bulkhead, see Hull section.')]
        return []

    @property
    def group_key(self) -> str:
        for note in self.notes:
            if note.category is NoteCategory.ITEM:
                return note.message
        return self.__class__.__name__

    def compute_cost(self) -> float:
        return self.cost

    def compute_power(self) -> float:
        return self.power

    def compute_tons(self) -> float:
        return self.tons

    def _refresh_field(self, field_name: str, compute_method_name: str) -> None:
        compute_method = getattr(type(self), compute_method_name)
        base_method = getattr(ShipPart, compute_method_name)
        if compute_method is base_method:
            return
        value = getattr(self, compute_method_name)()
        object.__setattr__(self, field_name, value)

    def refresh_derived_values(self) -> None:
        self._refresh_field('cost', 'compute_cost')
        self._refresh_field('power', 'compute_power')
        self._refresh_field('tons', 'compute_tons')

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)

    def bind(self, ship: ShipBase) -> None:
        self._ship = ship
        self.validate_tl()
        self.refresh_derived_values()
        self._refresh_armoured_bulkhead(ship)

    @property
    def ship(self) -> ShipBase:
        if self._ship is None:
            raise RuntimeError(f'{self.__class__.__name__} not bound to a Ship')
        return self._ship

    @property
    def ship_tl(self) -> int:
        return self.ship.tl

    @property
    def effective_tl(self) -> int:
        return self.ship_tl

    def validate_tl(self) -> None:
        if self.ship_tl < self.minimum_tl:
            self.error(
                f'Requires TL{self.minimum_tl}, ship is TL{self.ship_tl}',
            )

    def bulkhead_label(self) -> str:
        return self.build_item() or self.__class__.__name__

    def bulkhead_protected_tonnage(self) -> float:
        return self.tons

    def _refresh_armoured_bulkhead(self, ship: ShipBase) -> None:
        if not self.armoured_bulkhead:
            self._armoured_bulkhead_part = None
            return
        from .hull import ArmouredBulkhead

        bulkhead = ArmouredBulkhead(
            protected_tonnage=self.bulkhead_protected_tonnage(),
            protected_item=self.bulkhead_label(),
            from_ship_part=True,
        )
        bulkhead.bind(ship)
        self._armoured_bulkhead_part = bulkhead

    @property
    def armoured_bulkhead_part(self) -> ShipPart | None:
        return self._armoured_bulkhead_part


class CustomisableShipPart(ShipPart):
    customisation_grade: CustomisationGrade | None = None
    customisations: tuple[Customisation, ...] = ()
    possible_customisations: ClassVar[tuple[Customisation, ...]] = ()

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        self.validate_customisations()

    @property
    def group_key(self) -> str:
        base = super().group_key
        if not self.customisations:
            return base
        grade = self.customisation_grade.value if self.customisation_grade else ''
        suffix = '~'.join([grade, *[c.name for c in self.customisations]])
        return f'{base}|{suffix}'

    @property
    def allowed_customisation_names(self) -> set[str]:
        return {customisation.name for customisation in self.possible_customisations}

    @property
    def total_advantages(self) -> int:
        return sum(customisation.advantage for customisation in self.customisations)

    @property
    def total_disadvantages(self) -> int:
        return sum(customisation.disadvantage for customisation in self.customisations)

    @property
    def customisation_tl_delta(self) -> int:
        return (0 if self.customisation_grade is None else self.customisation_grade.tl_delta) + sum(
            customisation.tl_delta for customisation in self.customisations
        )

    @property
    def customisation_cost_multiplier(self) -> float:
        multiplier = 1.0 if self.customisation_grade is None else self.customisation_grade.base_cost_multiplier
        for customisation in self.customisations:
            multiplier *= customisation.cost_multiplier
        return multiplier

    @property
    def customisation_tons_multiplier(self) -> float:
        multiplier = 1.0 if self.customisation_grade is None else self.customisation_grade.base_tons_multiplier
        delta_percent = sum(customisation.tons_delta_percent for customisation in self.customisations)
        return multiplier * (1 + delta_percent)

    @property
    def customisation_power_multiplier(self) -> float:
        multiplier = 1.0
        for customisation in self.customisations:
            multiplier *= customisation.power_multiplier
        return multiplier

    @property
    def customisation_fuel_multiplier(self) -> float:
        multiplier = 1.0
        for customisation in self.customisations:
            multiplier *= customisation.fuel_multiplier
        return multiplier

    @property
    def customisation_notes(self) -> list[Note]:
        notes: list[Note] = []
        for customisation in self.customisations:
            notes.extend(customisation.build_notes())
        return notes

    def validate_customisations(self) -> None:
        for customisation in self.customisations:
            if customisation.name not in self.allowed_customisation_names:
                self.error(f'Customisation not allowed for {self.__class__.__name__}: {customisation.name}')

        if self.customisation_grade is None:
            if self.customisations:
                self.error('Customisations require a customisation grade')
            return

        expected_advantages = self.customisation_grade.required_advantages
        expected_disadvantages = self.customisation_grade.required_disadvantages
        if self.total_advantages != expected_advantages or self.total_disadvantages != expected_disadvantages:
            self.error(
                'Customisations do not match '
                f'{self.customisation_grade.value}: '
                f'expected {expected_advantages} advantage(s) and {expected_disadvantages} disadvantage(s), got '
                f'{self.total_advantages} and {self.total_disadvantages}'
            )


def grade_for_advantages(advantages: int) -> CustomisationGrade | None:
    return {
        0: None,
        1: CustomisationGrade.ADVANCED,
        2: CustomisationGrade.VERY_ADVANCED,
        3: CustomisationGrade.HIGH_TECHNOLOGY,
    }.get(advantages)


def grade_for_disadvantages(disadvantages: int) -> CustomisationGrade | None:
    return {
        0: None,
        1: CustomisationGrade.PROTOTYPE,
        2: CustomisationGrade.EARLY_PROTOTYPE,
    }.get(disadvantages)

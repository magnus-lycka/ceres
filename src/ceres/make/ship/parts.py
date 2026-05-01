from enum import StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field, PrivateAttr, TypeAdapter

from .base import CeresModel, Note, NoteCategory, ShipBase
from .text import collapse_repeated_labels


class CustomisationGrade(StrEnum):
    EARLY_PROTOTYPE = 'EARLY_PROTOTYPE'
    PROTOTYPE = 'PROTOTYPE'
    BUDGET = 'BUDGET'
    ADVANCED = 'ADVANCED'
    VERY_ADVANCED = 'VERY_ADVANCED'
    HIGH_TECHNOLOGY = 'HIGH_TECHNOLOGY'


class Modification(CeresModel):
    name: str
    advantage: int = 0
    disadvantage: int = 0
    cost_multiplier: float = 1.0
    tons_delta_percent: float = 0.0
    power_multiplier: float = 1.0
    fuel_delta_percent: float = 0.0
    tl_delta: int = 0
    info_notes: tuple[str, ...] = ()
    model_config = {'frozen': True}

    def build_item(self) -> str | None:
        return self.name

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message=message) for message in self.info_notes]


SizeReduction = Modification(name='Size Reduction', advantage=1, tons_delta_percent=-0.10)
IncreasedSize = Modification(name='Increased Size', disadvantage=1, tons_delta_percent=0.25)
EnergyEfficient = Modification(name='Energy Efficient', advantage=1, power_multiplier=0.75)
EnergyInefficient = Modification(name='Energy Inefficient', disadvantage=1, power_multiplier=1.25)


class Customisation(CeresModel):
    """Declared customisation grade with its modifications."""

    grade: CustomisationGrade
    modifications: tuple[Modification, ...]
    model_config = {'frozen': True}

    _cost_multiplier: ClassVar[float]
    _tons_multiplier: ClassVar[float]
    _tl_delta: ClassVar[int]
    _display_name: ClassVar[str]
    _required_advantages: ClassVar[int]
    _required_disadvantages: ClassVar[int]

    def __init__(self, *modifications: Modification, **kwargs):
        if modifications:
            kwargs['modifications'] = modifications
        super().__init__(**kwargs)

    def model_post_init(self, __context) -> None:
        self.notes.clear()
        total_adv = sum(m.advantage for m in self.modifications)
        total_dis = sum(m.disadvantage for m in self.modifications)
        if total_adv != self._required_advantages or total_dis != self._required_disadvantages:
            self.error(
                f'{self.__class__.__name__} requires '
                f'{self._required_advantages} advantage point(s) and '
                f'{self._required_disadvantages} disadvantage point(s), '
                f'got {total_adv} and {total_dis}'
            )

    @property
    def note_text(self) -> str:
        parts = collapse_repeated_labels(m.name for m in self.modifications)
        return f'{self._display_name}: {", ".join(parts)}'

    @property
    def cost_multiplier(self) -> float:
        result = self._cost_multiplier
        for m in self.modifications:
            result *= m.cost_multiplier
        return result

    @property
    def tons_multiplier(self) -> float:
        delta = sum(m.tons_delta_percent for m in self.modifications)
        return self._tons_multiplier * (1 + delta)

    @property
    def power_multiplier(self) -> float:
        result = 1.0
        for m in self.modifications:
            result *= m.power_multiplier
        return result

    @property
    def fuel_multiplier(self) -> float:
        return 1.0 + sum(m.fuel_delta_percent for m in self.modifications)

    @property
    def tl_delta(self) -> int:
        return self._tl_delta + sum(m.tl_delta for m in self.modifications)

    def check_ship_tl(self, part: CustomisableShipPart) -> None:
        available_tl = part.tl + self.tl_delta
        if part.ship_tl < available_tl:
            part.error(f'Requires TL{available_tl}, ship is TL{part.ship_tl}')
            return
        if self.tl_delta < 0 and part.ship_tl > available_tl:
            part.warning(f'{self._display_name} not required: ship TL{part.ship_tl} exceeds required TL{available_tl}')


class EarlyPrototype(Customisation):
    grade: Literal[CustomisationGrade.EARLY_PROTOTYPE] = CustomisationGrade.EARLY_PROTOTYPE
    _required_advantages: ClassVar[int] = 0
    _required_disadvantages: ClassVar[int] = 2
    _cost_multiplier: ClassVar[float] = 11.0
    _tons_multiplier: ClassVar[float] = 2.0
    _tl_delta: ClassVar[int] = -2
    _display_name: ClassVar[str] = 'Early Prototype'


class Prototype(Customisation):
    grade: Literal[CustomisationGrade.PROTOTYPE] = CustomisationGrade.PROTOTYPE
    _required_advantages: ClassVar[int] = 0
    _required_disadvantages: ClassVar[int] = 1
    _cost_multiplier: ClassVar[float] = 6.0
    _tons_multiplier: ClassVar[float] = 1.0
    _tl_delta: ClassVar[int] = -1
    _display_name: ClassVar[str] = 'Prototype'


class Budget(Customisation):
    grade: Literal[CustomisationGrade.BUDGET] = CustomisationGrade.BUDGET
    _required_advantages: ClassVar[int] = 0
    _required_disadvantages: ClassVar[int] = 1
    _cost_multiplier: ClassVar[float] = 0.75
    _tons_multiplier: ClassVar[float] = 1.0
    _tl_delta: ClassVar[int] = 0
    _display_name: ClassVar[str] = 'Budget'


class Advanced(Customisation):
    grade: Literal[CustomisationGrade.ADVANCED] = CustomisationGrade.ADVANCED
    _required_advantages: ClassVar[int] = 1
    _required_disadvantages: ClassVar[int] = 0
    _cost_multiplier: ClassVar[float] = 1.10
    _tons_multiplier: ClassVar[float] = 1.0
    _tl_delta: ClassVar[int] = 1
    _display_name: ClassVar[str] = 'Advanced'


class VeryAdvanced(Customisation):
    grade: Literal[CustomisationGrade.VERY_ADVANCED] = CustomisationGrade.VERY_ADVANCED
    _required_advantages: ClassVar[int] = 2
    _required_disadvantages: ClassVar[int] = 0
    _cost_multiplier: ClassVar[float] = 1.25
    _tons_multiplier: ClassVar[float] = 1.0
    _tl_delta: ClassVar[int] = 2
    _display_name: ClassVar[str] = 'Very Advanced'


class HighTechnology(Customisation):
    grade: Literal[CustomisationGrade.HIGH_TECHNOLOGY] = CustomisationGrade.HIGH_TECHNOLOGY
    _required_advantages: ClassVar[int] = 3
    _required_disadvantages: ClassVar[int] = 0
    _cost_multiplier: ClassVar[float] = 1.50
    _tons_multiplier: ClassVar[float] = 1.0
    _tl_delta: ClassVar[int] = 3
    _display_name: ClassVar[str] = 'High Technology'


CustomisationUnion = Annotated[
    EarlyPrototype | Prototype | Budget | Advanced | VeryAdvanced | HighTechnology,
    Field(discriminator='grade'),
]

_customisation_adapter: TypeAdapter[CustomisationUnion] = TypeAdapter(CustomisationUnion)


def _customisation_model_validate_json(cls, data, **kwargs):
    return _customisation_adapter.validate_json(data, **kwargs)


Customisation.model_validate_json = classmethod(_customisation_model_validate_json)


class ShipPart(CeresModel):
    cost: float = 0.0
    power: float = 0.0
    tons: float = 0.0
    armoured_bulkhead: bool = False
    _tl: ClassVar[int] = 0
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
        self.check_ship_tl()
        self.refresh_derived_values()
        if message := self.build_item():
            self.item(message)
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
    def tl(self) -> int:
        return self._tl

    def check_ship_tl(self) -> None:
        if self.ship_tl < self.tl:
            self.error(
                f'Requires TL{self.tl}, ship is TL{self.ship_tl}',
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
    customisation: CustomisationUnion | None = None
    allowed_modifications: ClassVar[frozenset[str]] = frozenset()

    @property
    def group_key(self) -> str:
        base = super().group_key
        if self.customisation is None:
            return base
        mods = ','.join(m.name for m in self.customisation.modifications)
        return f'{base}|{self.customisation.grade}~{mods}'

    def build_notes(self) -> list[Note]:
        notes = super().build_notes()
        if self.customisation is not None:
            notes.append(Note(category=NoteCategory.INFO, message=self.customisation.note_text))
        return notes

    def bind(self, ship: ShipBase) -> None:
        if self.customisation is not None:
            for mod in self.customisation.modifications:
                if mod.name not in self.allowed_modifications:
                    self.error(f'Modification not allowed for {self.__class__.__name__}: {mod.name}')
        super().bind(ship)

    def check_ship_tl(self) -> None:
        if self.customisation is None:
            super().check_ship_tl()
            return
        self.customisation.check_ship_tl(self)

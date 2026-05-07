from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field, PrivateAttr, TypeAdapter

from ceres.shared import CeresModel, CeresPart, NoteList, _Note

from .base import ShipBase
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

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        for message in self.info_notes:
            notes.info(message)
        return notes


SizeReduction = Modification(name='Size Reduction', advantage=1, tons_delta_percent=-0.10)
IncreasedSize = Modification(name='Increased Size', disadvantage=1, tons_delta_percent=0.25)
EnergyEfficient = Modification(name='Energy Efficient', advantage=1, power_multiplier=0.75)
EnergyInefficient = Modification(name='Energy Inefficient', disadvantage=1, power_multiplier=1.25)


class Customisation(CeresModel):
    """Declared customisation grade with its modifications."""

    notes: ClassVar[NoteList]
    grade: CustomisationGrade
    modifications: list[Modification]
    model_config = {'frozen': True}

    _cost_multiplier: ClassVar[float]
    _tons_multiplier: ClassVar[float]
    _tl_delta: ClassVar[int]
    _display_name: ClassVar[str]
    _required_advantages: ClassVar[int]
    _required_disadvantages: ClassVar[int]

    @property
    def notes(self) -> NoteList:
        notes = NoteList()
        total_adv = sum(m.advantage for m in self.modifications)
        total_dis = sum(m.disadvantage for m in self.modifications)
        if total_adv != self._required_advantages or total_dis != self._required_disadvantages:
            notes.error(
                f'{self.__class__.__name__} requires '
                f'{self._required_advantages} advantage point(s) and '
                f'{self._required_disadvantages} disadvantage point(s), '
                f'got {total_adv} and {total_dis}'
            )
        return notes

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

    def check_tl(self, part: CustomisableShipPart) -> None:
        available_tl = part.tl + self.tl_delta
        if part.assembly_tl < available_tl:
            part.error(f'Requires TL{available_tl}, ship is TL{part.assembly_tl}')
            return
        if self.tl_delta < 0 and part.assembly_tl > available_tl:
            part.warning(
                f'{self._display_name} not required: ship TL{part.assembly_tl} exceeds required TL{available_tl}'
            )

    @classmethod
    def model_validate_json(cls, json_data: str | bytes | bytearray, **kwargs: Any):
        if cls is Customisation:
            return _customisation_adapter.validate_json(json_data, **kwargs)
        return super().model_validate_json(json_data, **kwargs)


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


class ShipPartMixin(ABC):
    """Pure-Python ABC mixin for parts installable in a ship.

    Declares the contract that concrete ship-part classes must satisfy:
    ``assembly``, ``tons``, ``power``, and ``armoured_bulkhead``.

    Pydantic cannot see annotations on a plain mixin, so concrete classes must
    redeclare ``tons``, ``power``, and ``armoured_bulkhead`` as explicit Pydantic
    fields (and ``_armoured_bulkhead_part`` as a ``PrivateAttr``). The abstract
    declarations here make the requirement explicit and eliminate the "shadows an
    attribute" Pydantic warnings that plain class-variable defaults would trigger.
    """

    tons: float
    power: float
    armoured_bulkhead: bool
    cost: float
    tl: int
    notes: NoteList
    _armoured_bulkhead_part: ShipPart | None

    # ------------------------------------------------------------------
    # Ship binding
    # ------------------------------------------------------------------

    def bind(self, assembly: ShipBase) -> None:
        self._assembly = assembly
        self.check_tl()
        if message := self.build_item():
            self.item(message)
        self._refresh_armoured_bulkhead(assembly)

    @property
    @abstractmethod
    def assembly(self) -> ShipBase: ...

    @abstractmethod
    def build_item(self) -> str | None: ...

    @abstractmethod
    def item(self, message: str) -> None: ...

    @abstractmethod
    def error(self, message: str) -> None: ...

    @property
    def assembly_tl(self) -> int:
        return self.assembly.tl

    def check_tl(self) -> None:
        if self.assembly_tl < self.tl:
            self.error(f'Requires TL{self.tl}, ship is TL{self.assembly_tl}')

    # ------------------------------------------------------------------
    # Armoured bulkhead support
    # ------------------------------------------------------------------

    def bulkhead_label(self) -> str:
        return self.build_item() or self.__class__.__name__

    def bulkhead_protected_tonnage(self) -> float:
        return self.tons

    def _refresh_armoured_bulkhead(self, assembly: ShipBase) -> None:
        if not self.armoured_bulkhead:
            self._armoured_bulkhead_part = None
            return
        from .hull import ArmouredBulkhead

        bulkhead = ArmouredBulkhead(
            protected_tonnage=self.bulkhead_protected_tonnage(),
            protected_item=self.bulkhead_label(),
            from_ship_part=True,
        )
        bulkhead.bind(assembly)
        self._armoured_bulkhead_part = bulkhead

    @property
    def armoured_bulkhead_part(self) -> ShipPart | None:
        return self._armoured_bulkhead_part

    # ------------------------------------------------------------------
    # Grouping (used by spec table rendering)
    # ------------------------------------------------------------------

    @property
    def group_key(self) -> str:
        return self.notes.item_message or self.__class__.__name__


class ShipPart(CeresPart, ShipPartMixin):
    _armoured_bulkhead_part: ShipPart | None = PrivateAttr(default=None)
    tons: float = 0.0
    power: float = 0.0
    armoured_bulkhead: bool = False

    @property
    def assembly(self) -> ShipBase:
        a = self._assembly
        if a is None:
            raise RuntimeError(f'{type(self).__name__} not bound to an Assembly')
        if not isinstance(a, ShipBase):
            raise RuntimeError(f'{type(self).__name__} bound to unexpected assembly type {type(a).__name__}')
        return a

    def build_notes(self) -> list[_Note]:
        if self.armoured_bulkhead:
            notes = NoteList()
            notes.info('Armoured bulkhead, see Hull section.')
            return notes
        return []

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)


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

    @property
    def tons_multiplier(self) -> float:
        if self.customisation is None:
            return 1.0
        return self.customisation.tons_multiplier

    @property
    def cost_multiplier(self) -> float:
        if self.customisation is None:
            return 1.0
        return self.customisation.cost_multiplier

    @property
    def power_multiplier(self) -> float:
        if self.customisation is None:
            return 1.0
        return self.customisation.power_multiplier

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        if self.customisation is not None:
            notes.info(self.customisation.note_text)
        return notes

    def bind(self, assembly: ShipBase) -> None:
        if self.customisation is not None:
            for mod in self.customisation.modifications:
                if mod.name not in self.allowed_modifications:
                    self.error(f'Modification not allowed for {self.__class__.__name__}: {mod.name}')
        super().bind(assembly)

    def check_tl(self) -> None:
        if self.customisation is None:
            super().check_tl()
            return
        self.customisation.check_tl(self)

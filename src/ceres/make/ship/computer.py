from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field, PrivateAttr, field_validator, model_validator

from ceres.gear.computer import ComputerPart
from ceres.gear.software import Intellect, SoftwarePackage

from .base import CeresModel, Note, NoteCategory
from .parts import ShipPart, ShipPartMixin
from .software import JumpControl, Library, Manoeuvre, ShipSoftware
from .spec import ShipSpec, SpecRow, SpecSection


class ComputerBase(ComputerPart, ShipPartMixin):
    kind: str
    bis: bool = False
    fib: bool = False
    _label: ClassVar[str]
    _specs: ClassVar[dict[int, dict[str, int | float]]]
    _armoured_bulkhead_part: ShipPart | None = PrivateAttr(default=None)
    tons: float = 0.0
    power: float = 0.0
    armoured_bulkhead: bool = False

    @model_validator(mode='before')
    @classmethod
    def _fill_tl(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'tl' not in data:
            processing = data.get('processing')
            if processing is not None and processing in cls._specs:
                data = {**data, 'tl': int(cls._specs[processing]['tl'])}
        return data

    @field_validator('processing')
    @classmethod
    def validate_processing(cls, value: int) -> int:
        if value not in cls._specs:
            allowed = ', '.join(str(v) for v in sorted(cls._specs))
            raise ValueError(f'Unsupported {cls.__name__} processing {value}; expected one of: {allowed}')
        return value

    @property
    def description(self) -> str:
        return f'{self._label}/{self.processing}'

    @property
    def base_cost(self) -> float:
        return float(self._specs[self.processing]['cost'])

    def build_notes(self) -> list[Note]:
        if self.armoured_bulkhead:
            return [Note(category=NoteCategory.INFO, message='Armoured bulkhead, see Hull section.')]
        return []

    def build_item(self) -> str | None:
        item = self.description
        if self.bis:
            item += '/bis'
        if self.fib:
            item += '/fib'
        return item

    def check_tl(self) -> None:
        if self.assembly_tl < self.tl:
            self.error(f'Requires TL{self.tl}, ship is TL{self.assembly_tl}')

    @property
    def jump_control_processing(self) -> int:
        bonus = 5 if self.bis else 0
        return self.processing + bonus

    @property
    def included_software(self) -> list[SoftwarePackage]:
        packages: list[SoftwarePackage] = [Library(), Manoeuvre()]
        if self.assembly_tl >= 11:  # Intellect minimum TL
            packages.append(Intellect(rating=0))
        return packages

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        multiplier = 1.0
        if self.bis:
            multiplier += 0.5
        if self.fib:
            multiplier += 0.5
        return self.base_cost * multiplier


class Computer(ComputerBase):
    kind: Literal['computer'] = 'computer'
    _label = 'Computer'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        5: dict(tl=7, cost=30_000.0),
        10: dict(tl=9, cost=160_000.0),
        15: dict(tl=11, cost=2_000_000.0),
        20: dict(tl=12, cost=5_000_000.0),
        25: dict(tl=13, cost=10_000_000.0),
        30: dict(tl=14, cost=20_000_000.0),
        35: dict(tl=15, cost=30_000_000.0),
    }


class Core(ComputerBase):
    kind: Literal['core'] = 'core'
    _label = 'Core'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        40: dict(tl=9, cost=45_000_000.0),
        50: dict(tl=10, cost=60_000_000.0),
        60: dict(tl=11, cost=75_000_000.0),
        70: dict(tl=12, cost=80_000_000.0),
        80: dict(tl=13, cost=95_000_000.0),
        90: dict(tl=14, cost=120_000_000.0),
        100: dict(tl=15, cost=130_000_000.0),
    }


ShipComputer = Annotated[
    Computer | Core,
    Field(discriminator='kind'),
]


class ComputerSection(CeresModel):
    hardware: ShipComputer | None = None
    backup_hardware: ShipComputer | None = None
    software: list[ShipSoftware] = Field(default_factory=list)
    _software_packages: dict[type[SoftwarePackage], SoftwarePackage] = PrivateAttr(default_factory=dict)

    @property
    def software_packages(self) -> dict[type[SoftwarePackage], SoftwarePackage]:
        if not self._software_packages:
            self.refresh_software_packages()
        return self._software_packages

    def refresh_software_packages(self) -> None:
        packages: list[SoftwarePackage] = []
        if self.hardware is not None:
            packages.extend(package.model_copy(deep=True) for package in self.hardware.included_software)
        packages.extend(package.model_copy(deep=True) for package in self.software)
        selected: dict[type[SoftwarePackage], SoftwarePackage] = {}
        redundant: dict[type[SoftwarePackage], list[str]] = {}
        for package in packages:
            key = type(package)
            current = selected.get(key)
            if current is None:
                selected[key] = package
                continue
            if getattr(package, 'rating', 0) > getattr(current, 'rating', 0):
                redundant.setdefault(key, []).append(f'Redundant {current.description} added')
                selected[key] = package
                continue
            redundant.setdefault(key, []).append(f'Redundant {package.description} added')
        for key, package in selected.items():
            for message in redundant.get(key, []):
                package.warning(message)
        object.__setattr__(self, '_software_packages', selected)

    def validate_software(self) -> None:
        if self.hardware is None:
            for package in self.software_packages.values():
                package.warning('Ship software requires a computer')
            return
        if self.backup_hardware is not None and self.hardware.processing <= self.backup_hardware.processing:
            self.backup_hardware.error('Backup computer must have lower Processing than primary computer')
        for package in self.software_packages.values():
            package.validate_on_computer(self.hardware)

    def validate_jump_drive(self, drives) -> None:
        jump_control = self.software_packages.get(JumpControl)
        if not isinstance(jump_control, JumpControl):
            return
        effective = jump_control.effective_rating
        if effective is None:
            return
        if drives is None or drives.j_drive is None:
            jump_control.warning('No jump drive installed')
            return
        if effective > drives.j_drive.level:
            jump_control.warning(f'Limited to Jump {drives.j_drive.level} by drive capacity')

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        if self.hardware is not None:
            parts.append(self.hardware)  # ty: ignore[invalid-argument-type]
        if self.backup_hardware is not None:
            parts.append(self.backup_hardware)  # ty: ignore[invalid-argument-type]
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.hardware is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.COMPUTER, self.hardware))
        if self.backup_hardware is not None:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.COMPUTER,
                    self.backup_hardware,
                    item=f'Backup {ship._item_text(self.backup_hardware, self.backup_hardware.description)}',
                )
            )
        for package in self.software_packages.values():
            spec.add_row(
                SpecRow(
                    section=SpecSection.COMPUTER,
                    item=ship._item_text(package, package.description),
                    cost=package.cost or None,
                    notes=ship._display_notes(package),
                )
            )

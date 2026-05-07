from typing import Annotated, ClassVar, Literal, cast

from pydantic import Field, PrivateAttr

from ceres.gear.computer import ComputerPart
from ceres.gear.software import Intellect, SoftwarePackage
from ceres.shared import CeresModel, NoteList, _Note

from .parts import ShipPart, ShipPartMixin
from .software import JumpControl, Library, Manoeuvre, ShipSoftware
from .spec import ShipSpec, SpecRow, SpecSection


class ComputerBase(ComputerPart, ShipPartMixin):
    kind: str
    bis: bool = False
    fib: bool = False
    _label: ClassVar[str]
    _base_cost: ClassVar[float]
    _armoured_bulkhead_part: ShipPart | None = PrivateAttr(default=None)
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    armoured_bulkhead: bool = False

    @property
    def description(self) -> str:
        return f'{self._label}/{self.processing}'

    @property
    def base_cost(self) -> float:
        return self._base_cost

    def build_notes(self) -> list[_Note]:
        if self.armoured_bulkhead:
            notes = NoteList()
            notes.info('Armoured bulkhead, see Hull section.')
            return notes
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

    def can_run_jump_control(self, required_processing: int) -> bool:
        bonus = 5 if self.bis else 0
        return self.processing + bonus >= required_processing

    @property
    def included_software(self) -> list[SoftwarePackage]:
        packages: list[SoftwarePackage] = [Library(), Manoeuvre()]
        if self.assembly_tl >= 11:  # Intellect minimum TL
            packages.append(Intellect(rating=0))
        return packages

    @property
    def tons(self) -> float:
        return 0.0

    @property
    def cost(self) -> float:
        multiplier = 1.0
        if self.bis:
            multiplier += 0.5
        if self.fib:
            multiplier += 0.5
        return self.base_cost * multiplier

    @property
    def power(self) -> float:
        return 0.0


class _Computer(ComputerBase):
    _label = 'Computer'


class Computer5(_Computer):
    kind: Literal['computer_5'] = 'computer_5'
    processing: Literal[5] = 5
    tl: int = 7
    _base_cost = 30_000.0


class Computer10(_Computer):
    kind: Literal['computer_10'] = 'computer_10'
    processing: Literal[10] = 10
    tl: int = 9
    _base_cost = 160_000.0


class Computer15(_Computer):
    kind: Literal['computer_15'] = 'computer_15'
    processing: Literal[15] = 15
    tl: int = 11
    _base_cost = 2_000_000.0


class Computer20(_Computer):
    kind: Literal['computer_20'] = 'computer_20'
    processing: Literal[20] = 20
    tl: int = 12
    _base_cost = 5_000_000.0


class Computer25(_Computer):
    kind: Literal['computer_25'] = 'computer_25'
    processing: Literal[25] = 25
    tl: int = 13
    _base_cost = 10_000_000.0


class Computer30(_Computer):
    kind: Literal['computer_30'] = 'computer_30'
    processing: Literal[30] = 30
    tl: int = 14
    _base_cost = 20_000_000.0


class Computer35(_Computer):
    kind: Literal['computer_35'] = 'computer_35'
    processing: Literal[35] = 35
    tl: int = 15
    _base_cost = 30_000_000.0


type Computer = Annotated[
    Computer5 | Computer10 | Computer15 | Computer20 | Computer25 | Computer30 | Computer35,
    Field(discriminator='kind'),
]


class _Core(ComputerBase):
    _label = 'Core'

    def can_run_jump_control(self, required_processing: int) -> bool:
        return True


class Core40(_Core):
    kind: Literal['core_40'] = 'core_40'
    processing: Literal[40] = 40
    tl: int = 9
    _base_cost = 45_000_000.0


class Core50(_Core):
    kind: Literal['core_50'] = 'core_50'
    processing: Literal[50] = 50
    tl: int = 10
    _base_cost = 60_000_000.0


class Core60(_Core):
    kind: Literal['core_60'] = 'core_60'
    processing: Literal[60] = 60
    tl: int = 11
    _base_cost = 75_000_000.0


class Core70(_Core):
    kind: Literal['core_70'] = 'core_70'
    processing: Literal[70] = 70
    tl: int = 12
    _base_cost = 80_000_000.0


class Core80(_Core):
    kind: Literal['core_80'] = 'core_80'
    processing: Literal[80] = 80
    tl: int = 13
    _base_cost = 95_000_000.0


class Core90(_Core):
    kind: Literal['core_90'] = 'core_90'
    processing: Literal[90] = 90
    tl: int = 14
    _base_cost = 120_000_000.0


class Core100(_Core):
    kind: Literal['core_100'] = 'core_100'
    processing: Literal[100] = 100
    tl: int = 15
    _base_cost = 130_000_000.0


type Core = Annotated[
    Core40 | Core50 | Core60 | Core70 | Core80 | Core90 | Core100,
    Field(discriminator='kind'),
]


ShipComputer = Annotated[
    Computer5
    | Computer10
    | Computer15
    | Computer20
    | Computer25
    | Computer30
    | Computer35
    | Core40
    | Core50
    | Core60
    | Core70
    | Core80
    | Core90
    | Core100,
    Field(discriminator='kind'),
]


class ComputerSection(CeresModel):
    hardware: ShipComputer
    backup_hardware: ShipComputer | None = None
    software: list[ShipSoftware] = Field(default_factory=list)

    @property
    def software_packages(self) -> list[SoftwarePackage]:
        return [*self.hardware.included_software, *self.software]

    def validate_software(self) -> None:
        if self.backup_hardware is not None and self.hardware.processing <= self.backup_hardware.processing:
            self.backup_hardware.error('Backup computer must have lower Processing than primary computer')
        for package in self.software:
            package.validate_on_computer(self.hardware)

    def validate_jump_drive(self, drives) -> None:
        jump_control = next((package for package in self.software_packages if isinstance(package, JumpControl)), None)
        if jump_control is None:
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
        parts: list[ShipPart] = [cast(ShipPart, self.hardware)]
        if self.backup_hardware is not None:
            parts.append(cast(ShipPart, self.backup_hardware))
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        spec.add_row(ship._spec_row_for_part(SpecSection.COMPUTER, self.hardware))
        if self.backup_hardware is not None:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.COMPUTER,
                    self.backup_hardware,
                    item=f'Backup {ship._item_text(self.backup_hardware, self.backup_hardware.description)}',
                )
            )
        for package in self.software_packages:
            spec.add_row(
                SpecRow(
                    section=SpecSection.COMPUTER,
                    item=ship._item_text(package, package.description),
                    cost=package.cost or None,
                    notes=ship._display_notes(package),
                )
            )

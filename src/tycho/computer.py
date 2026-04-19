from typing import Annotated, ClassVar, Literal

from pydantic import Field, PrivateAttr

from .base import CeresModel
from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection


class SoftwarePackage(CeresModel):
    description: str
    minimum_tl: ClassVar[int]
    bandwidth: ClassVar[int]
    base_cost: ClassVar[float]
    model_config = {'frozen': True}

    @property
    def cost(self) -> float:
        return self.base_cost

    @property
    def name(self) -> str:
        return self.description

    @property
    def tons(self) -> float:
        return 0.0

    def build_item(self) -> str | None:
        return self.description

    @property
    def singleton_type(self) -> type[SoftwarePackage]:
        return type(self)

    @property
    def singleton_rank(self) -> int:
        return 0


class Library(SoftwarePackage):
    description: Literal['Library'] = 'Library'
    minimum_tl = 8
    bandwidth = 0
    base_cost = 0.0


class Manoeuvre(SoftwarePackage):
    description: Literal['Manoeuvre/0'] = 'Manoeuvre/0'
    minimum_tl = 8
    bandwidth = 0
    base_cost = 0.0


class Intellect(SoftwarePackage):
    description: Literal['Intellect'] = 'Intellect'
    minimum_tl = 11
    bandwidth = 0
    base_cost = 0.0


class JumpControl(SoftwarePackage):
    rating: int

    @property
    def singleton_type(self) -> type[SoftwarePackage]:
        return JumpControl

    @property
    def singleton_rank(self) -> int:
        return self.rating


class JumpControl1(JumpControl):
    description: Literal['Jump Control/1'] = 'Jump Control/1'
    minimum_tl = 9
    bandwidth = 5
    base_cost = 100_000.0
    rating: Literal[1] = 1


class JumpControl2(JumpControl):
    description: Literal['Jump Control/2'] = 'Jump Control/2'
    minimum_tl = 11
    bandwidth = 10
    base_cost = 200_000.0
    rating: Literal[2] = 2


class JumpControl3(JumpControl):
    description: Literal['Jump Control/3'] = 'Jump Control/3'
    minimum_tl = 12
    bandwidth = 15
    base_cost = 300_000.0
    rating: Literal[3] = 3


class JumpControl4(JumpControl):
    description: Literal['Jump Control/4'] = 'Jump Control/4'
    minimum_tl = 13
    bandwidth = 20
    base_cost = 400_000.0
    rating: Literal[4] = 4


class JumpControl5(JumpControl):
    description: Literal['Jump Control/5'] = 'Jump Control/5'
    minimum_tl = 14
    bandwidth = 25
    base_cost = 500_000.0
    rating: Literal[5] = 5


class JumpControl6(JumpControl):
    description: Literal['Jump Control/6'] = 'Jump Control/6'
    minimum_tl = 15
    bandwidth = 30
    base_cost = 600_000.0
    rating: Literal[6] = 6


class AutoRepair(SoftwarePackage):
    rating: int

    @property
    def singleton_type(self) -> type[SoftwarePackage]:
        return AutoRepair

    @property
    def singleton_rank(self) -> int:
        return self.rating


class AutoRepair1(AutoRepair):
    description: Literal['Auto-Repair/1'] = 'Auto-Repair/1'
    minimum_tl = 11
    bandwidth = 10
    base_cost = 5_000_000.0
    rating: Literal[1] = 1


class AutoRepair2(AutoRepair):
    description: Literal['Auto-Repair/2'] = 'Auto-Repair/2'
    minimum_tl = 12
    bandwidth = 20
    base_cost = 10_000_000.0
    rating: Literal[2] = 2


class FireControl(SoftwarePackage):
    rating: int

    @property
    def singleton_type(self) -> type[SoftwarePackage]:
        return FireControl

    @property
    def singleton_rank(self) -> int:
        return self.rating


class FireControl1(FireControl):
    description: Literal['Fire Control/1'] = 'Fire Control/1'
    minimum_tl = 9
    bandwidth = 5
    base_cost = 2_000_000.0
    rating: Literal[1] = 1


class FireControl2(FireControl):
    description: Literal['Fire Control/2'] = 'Fire Control/2'
    minimum_tl = 11
    bandwidth = 10
    base_cost = 4_000_000.0
    rating: Literal[2] = 2


class FireControl3(FireControl):
    description: Literal['Fire Control/3'] = 'Fire Control/3'
    minimum_tl = 12
    bandwidth = 15
    base_cost = 6_000_000.0
    rating: Literal[3] = 3


class FireControl4(FireControl):
    description: Literal['Fire Control/4'] = 'Fire Control/4'
    minimum_tl = 13
    bandwidth = 20
    base_cost = 8_000_000.0
    rating: Literal[4] = 4


class FireControl5(FireControl):
    description: Literal['Fire Control/5'] = 'Fire Control/5'
    minimum_tl = 14
    bandwidth = 25
    base_cost = 10_000_000.0
    rating: Literal[5] = 5


class Evade(SoftwarePackage):
    rating: int

    @property
    def singleton_type(self) -> type[SoftwarePackage]:
        return Evade

    @property
    def singleton_rank(self) -> int:
        return self.rating


class Evade1(Evade):
    description: Literal['Evade/1'] = 'Evade/1'
    minimum_tl = 9
    bandwidth = 5
    base_cost = 1_000_000.0
    rating: Literal[1] = 1


class Evade2(Evade):
    description: Literal['Evade/2'] = 'Evade/2'
    minimum_tl = 11
    bandwidth = 10
    base_cost = 2_000_000.0
    rating: Literal[2] = 2


class Evade3(Evade):
    description: Literal['Evade/3'] = 'Evade/3'
    minimum_tl = 12
    bandwidth = 15
    base_cost = 3_000_000.0
    rating: Literal[3] = 3


class Computer(ShipPart):
    description: str
    minimum_tl: ClassVar[int]
    processing: ClassVar[int]
    base_cost: ClassVar[float]
    bis: bool = False
    fib: bool = False
    retro: bool = False

    def build_item(self) -> str | None:
        item = self.description
        if self.bis:
            item += '/bis'
        if self.fib:
            item += '/fib'
        if self.retro:
            item += ', (Retro*)'
        return item

    @property
    def effective_tl(self):
        return self.ship_tl

    @property
    def jump_control_processing(self) -> int:
        bonus = 5 if self.bis else 0
        return self.processing + bonus

    @property
    def included_software(self) -> list[SoftwarePackage]:
        packages: list[SoftwarePackage] = [Library(), Manoeuvre()]
        if self.ship_tl >= Intellect.minimum_tl:
            packages.append(Intellect())
        return packages

    def can_run(self, package: SoftwarePackage) -> bool:
        if self.ship_tl < package.minimum_tl:
            return False
        if isinstance(package, JumpControl):
            if isinstance(self, Core):
                return True
            return self.jump_control_processing >= package.bandwidth
        return self.processing >= package.bandwidth

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        multiplier = 1.0
        if self.bis:
            multiplier += 0.5
        if self.fib:
            multiplier += 0.5
        cost = self.base_cost * multiplier
        if self.retro:
            cost *= 0.5 ** max(self.ship_tl - self.minimum_tl, 0)
        return cost


class Computer5(Computer):
    description: Literal['Computer/5'] = 'Computer/5'
    minimum_tl = 7
    processing = 5
    base_cost = 30_000.0


class Computer10(Computer):
    description: Literal['Computer/10'] = 'Computer/10'
    minimum_tl = 9
    processing = 10
    base_cost = 160_000.0


class Computer15(Computer):
    description: Literal['Computer/15'] = 'Computer/15'
    minimum_tl = 11
    processing = 15
    base_cost = 2_000_000.0


class Computer20(Computer):
    description: Literal['Computer/20'] = 'Computer/20'
    minimum_tl = 12
    processing = 20
    base_cost = 5_000_000.0


class Computer25(Computer):
    description: Literal['Computer/25'] = 'Computer/25'
    minimum_tl = 13
    processing = 25
    base_cost = 10_000_000.0


class Computer30(Computer):
    description: Literal['Computer/30'] = 'Computer/30'
    minimum_tl = 14
    processing = 30
    base_cost = 20_000_000.0


class Computer35(Computer):
    description: Literal['Computer/35'] = 'Computer/35'
    minimum_tl = 15
    processing = 35
    base_cost = 30_000_000.0


class Core(Computer):
    pass


class Core40(Core):
    description: Literal['Core/40'] = 'Core/40'
    minimum_tl = 9
    processing = 40
    base_cost = 45_000_000.0


class Core50(Core):
    description: Literal['Core/50'] = 'Core/50'
    minimum_tl = 10
    processing = 50
    base_cost = 60_000_000.0


class Core60(Core):
    description: Literal['Core/60'] = 'Core/60'
    minimum_tl = 11
    processing = 60
    base_cost = 75_000_000.0


class Core70(Core):
    description: Literal['Core/70'] = 'Core/70'
    minimum_tl = 12
    processing = 70
    base_cost = 80_000_000.0


class Core80(Core):
    description: Literal['Core/80'] = 'Core/80'
    minimum_tl = 13
    processing = 80
    base_cost = 95_000_000.0


class Core90(Core):
    description: Literal['Core/90'] = 'Core/90'
    minimum_tl = 14
    processing = 90
    base_cost = 120_000_000.0


class Core100(Core):
    description: Literal['Core/100'] = 'Core/100'
    minimum_tl = 15
    processing = 100
    base_cost = 130_000_000.0


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
    Field(discriminator='description'),
]

ShipSoftware = Annotated[
    Library
    | Manoeuvre
    | Intellect
    | JumpControl1
    | JumpControl2
    | JumpControl3
    | JumpControl4
    | JumpControl5
    | JumpControl6
    | AutoRepair1
    | AutoRepair2
    | FireControl1
    | FireControl2
    | FireControl3
    | FireControl4
    | FireControl5
    | Evade1
    | Evade2
    | Evade3,
    Field(discriminator='description'),
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
            key = package.singleton_type
            current = selected.get(key)
            if current is None:
                selected[key] = package
                continue
            if package.singleton_rank > current.singleton_rank:
                redundant.setdefault(key, []).append(f'Redundant {current.description} added')
                selected[key] = package
                continue
            redundant.setdefault(key, []).append(f'Redundant {package.description} added')
        for key, package in selected.items():
            for message in redundant.get(key, []):
                package.warning(message)
        object.__setattr__(self, '_software_packages', selected)

    def validate_software(self, ship_tl: int) -> None:
        if self.hardware is None:
            for package in self.software_packages.values():
                package.warning('Ship software requires a computer')
            return
        if self.backup_hardware is not None and self.hardware.processing <= self.backup_hardware.processing:
            self.backup_hardware.error('Backup computer must have lower Processing than primary computer')
        for package in self.software_packages.values():
            if ship_tl < package.minimum_tl:
                package.error(f'{package.description} requires TL{package.minimum_tl}')
            if not self.hardware.can_run(package):
                package.error(f'{self.hardware.description} cannot run {package.description}')

    def validate_jump_drive(self, drives) -> None:
        jump_control = self.software_packages.get(JumpControl)
        if not isinstance(jump_control, JumpControl):
            return
        if drives is None or drives.jump_drive is None:
            jump_control.warning('No jump drive installed')
            return
        if jump_control.rating > drives.jump_drive.rating:
            jump_control.warning(f'Limited to Jump {drives.jump_drive.rating} by drive capacity')

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = []
        if self.hardware is not None:
            parts.append(self.hardware)
        if self.backup_hardware is not None:
            parts.append(self.backup_hardware)
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

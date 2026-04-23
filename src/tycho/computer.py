from typing import Annotated, ClassVar, Literal

from pydantic import Field, PrivateAttr, field_validator

from .base import CeresModel
from .parts import ShipPart
from .spec import ShipSpec, SpecRow, SpecSection


class SoftwarePackage(CeresModel):
    package: str
    model_config = {'frozen': True}

    @property
    def description(self) -> str:
        raise NotImplementedError

    @property
    def cost(self) -> float:
        return 0.0

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


class FixedSoftwarePackage(SoftwarePackage):
    label: ClassVar[str]
    minimum_tl: ClassVar[int]
    bandwidth: ClassVar[int]
    base_cost: ClassVar[float]

    @property
    def description(self) -> str:
        return self.label

    @property
    def cost(self) -> float:
        return self.base_cost


class Library(FixedSoftwarePackage):
    package: Literal['library'] = 'library'
    label = 'Library'
    minimum_tl = 8
    bandwidth = 0
    base_cost = 0.0


class Manoeuvre(FixedSoftwarePackage):
    package: Literal['manoeuvre'] = 'manoeuvre'
    label = 'Manoeuvre/0'
    minimum_tl = 8
    bandwidth = 0
    base_cost = 0.0


class Intellect(FixedSoftwarePackage):
    package: Literal['intellect'] = 'intellect'
    label = 'Intellect'
    minimum_tl = 11
    bandwidth = 0
    base_cost = 0.0


class RatedSoftwarePackage(SoftwarePackage):
    rating: int
    label: ClassVar[str]
    _specs: ClassVar[dict[int, dict[str, int | float]]]

    def __init__(self, rating: int | None = None, /, **data):
        if rating is not None and 'rating' not in data:
            data['rating'] = rating
        super().__init__(**data)

    @field_validator('rating')
    @classmethod
    def validate_rating(cls, value: int) -> int:
        if value not in cls._specs:
            allowed = ', '.join(str(v) for v in sorted(cls._specs))
            raise ValueError(f'Unsupported {cls.__name__} rating {value}; expected one of: {allowed}')
        return value

    @property
    def bandwidth(self) -> int:
        return int(self._specs[self.rating]['bandwidth'])

    @property
    def minimum_tl(self) -> int:
        return int(self._specs[self.rating]['minimum_tl'])

    @property
    def cost(self) -> float:
        return float(self._specs[self.rating]['cost'])

    @property
    def description(self) -> str:
        return f'{self.label}/{self.rating}'

    @property
    def singleton_rank(self) -> int:
        return self.rating


class JumpControl(RatedSoftwarePackage):
    package: Literal['jump_control'] = 'jump_control'
    label = 'Jump Control'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=5, minimum_tl=9, cost=100_000.0),
        2: dict(bandwidth=10, minimum_tl=11, cost=200_000.0),
        3: dict(bandwidth=15, minimum_tl=12, cost=300_000.0),
        4: dict(bandwidth=20, minimum_tl=13, cost=400_000.0),
        5: dict(bandwidth=25, minimum_tl=14, cost=500_000.0),
        6: dict(bandwidth=30, minimum_tl=15, cost=600_000.0),
    }


class AutoRepair(RatedSoftwarePackage):
    package: Literal['auto_repair'] = 'auto_repair'
    label = 'Auto-Repair'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=10, minimum_tl=11, cost=5_000_000.0),
        2: dict(bandwidth=20, minimum_tl=12, cost=10_000_000.0),
    }


class FireControl(RatedSoftwarePackage):
    package: Literal['fire_control'] = 'fire_control'
    label = 'Fire Control'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=5, minimum_tl=9, cost=2_000_000.0),
        2: dict(bandwidth=10, minimum_tl=11, cost=4_000_000.0),
        3: dict(bandwidth=15, minimum_tl=12, cost=6_000_000.0),
        4: dict(bandwidth=20, minimum_tl=13, cost=8_000_000.0),
        5: dict(bandwidth=25, minimum_tl=14, cost=10_000_000.0),
    }


class AdvancedFireControl(RatedSoftwarePackage):
    package: Literal['advanced_fire_control'] = 'advanced_fire_control'
    label = 'Advanced Fire Control'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=15, minimum_tl=10, cost=12_000_000.0),
        2: dict(bandwidth=25, minimum_tl=12, cost=15_000_000.0),
        3: dict(bandwidth=30, minimum_tl=14, cost=18_000_000.0),
    }


class AntiHijack(RatedSoftwarePackage):
    package: Literal['anti_hijack'] = 'anti_hijack'
    label = 'Anti-Hijack'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=2, minimum_tl=11, cost=6_000_000.0),
        2: dict(bandwidth=10, minimum_tl=12, cost=8_000_000.0),
        3: dict(bandwidth=15, minimum_tl=13, cost=10_000_000.0),
    }


class Evade(RatedSoftwarePackage):
    package: Literal['evade'] = 'evade'
    label = 'Evade'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=5, minimum_tl=9, cost=1_000_000.0),
        2: dict(bandwidth=10, minimum_tl=11, cost=2_000_000.0),
        3: dict(bandwidth=15, minimum_tl=12, cost=3_000_000.0),
    }


class BroadSpectrumEW(FixedSoftwarePackage):
    package: Literal['broad_spectrum_ew'] = 'broad_spectrum_ew'
    label = 'Broad Spectrum EW'
    minimum_tl = 13
    bandwidth = 12
    base_cost = 14_000_000.0


class ElectronicWarfare(RatedSoftwarePackage):
    package: Literal['electronic_warfare'] = 'electronic_warfare'
    label = 'Electronic Warfare'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=10, minimum_tl=10, cost=15_000_000.0),
        2: dict(bandwidth=15, minimum_tl=13, cost=18_000_000.0),
        3: dict(bandwidth=20, minimum_tl=15, cost=24_000_000.0),
    }


class VirtualGunner(RatedSoftwarePackage):
    package: Literal['virtual_gunner'] = 'virtual_gunner'
    label = 'Virtual Gunner'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: dict(bandwidth=5, minimum_tl=9, cost=1_000_000.0),
        1: dict(bandwidth=10, minimum_tl=12, cost=5_000_000.0),
        2: dict(bandwidth=15, minimum_tl=15, cost=10_000_000.0),
    }


class ComputerBase(ShipPart):
    kind: str
    score: int
    bis: bool = False
    fib: bool = False
    _label: ClassVar[str]
    _specs: ClassVar[dict[int, dict[str, int | float]]]

    def __init__(self, score: int | None = None, /, **data):
        if score is not None and 'score' not in data:
            data['score'] = score
        super().__init__(**data)

    @field_validator('score')
    @classmethod
    def validate_score(cls, value: int) -> int:
        if value not in cls._specs:
            allowed = ', '.join(str(v) for v in sorted(cls._specs))
            raise ValueError(f'Unsupported {cls.__name__} score {value}; expected one of: {allowed}')
        return value

    @property
    def description(self) -> str:
        return f'{self._label}/{self.score}'

    @property
    def minimum_tl(self) -> int:
        return int(self._specs[self.score]['minimum_tl'])

    @property
    def processing(self) -> int:
        return self.score

    @property
    def base_cost(self) -> float:
        return float(self._specs[self.score]['cost'])

    def build_item(self) -> str | None:
        item = self.description
        if self.bis:
            item += '/bis'
        if self.fib:
            item += '/fib'
        return item

    @property
    def effective_tl(self):
        return self.ship_tl

    def validate_tl(self) -> None:
        if self.ship_tl < self.minimum_tl:
            self.error(f'Requires TL{self.minimum_tl}, ship is TL{self.ship_tl}')

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
        return self.base_cost * multiplier


class Computer(ComputerBase):
    kind: Literal['computer'] = 'computer'
    _label = 'Computer'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        5: dict(minimum_tl=7, cost=30_000.0),
        10: dict(minimum_tl=9, cost=160_000.0),
        15: dict(minimum_tl=11, cost=2_000_000.0),
        20: dict(minimum_tl=12, cost=5_000_000.0),
        25: dict(minimum_tl=13, cost=10_000_000.0),
        30: dict(minimum_tl=14, cost=20_000_000.0),
        35: dict(minimum_tl=15, cost=30_000_000.0),
    }


class Core(ComputerBase):
    kind: Literal['core'] = 'core'
    _label = 'Core'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        40: dict(minimum_tl=9, cost=45_000_000.0),
        50: dict(minimum_tl=10, cost=60_000_000.0),
        60: dict(minimum_tl=11, cost=75_000_000.0),
        70: dict(minimum_tl=12, cost=80_000_000.0),
        80: dict(minimum_tl=13, cost=95_000_000.0),
        90: dict(minimum_tl=14, cost=120_000_000.0),
        100: dict(minimum_tl=15, cost=130_000_000.0),
    }


ShipComputer = Annotated[
    Computer | Core,
    Field(discriminator='kind'),
]

ShipSoftware = Annotated[
    Library
    | Manoeuvre
    | Intellect
    | JumpControl
    | AutoRepair
    | FireControl
    | AdvancedFireControl
    | AntiHijack
    | Evade
    | BroadSpectrumEW
    | ElectronicWarfare
    | VirtualGunner,
    Field(discriminator='package'),
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
        if drives is None or drives.j_drive is None:
            jump_control.warning('No jump drive installed')
            return
        if jump_control.rating > drives.j_drive.level:
            jump_control.warning(f'Limited to Jump {drives.j_drive.level} by drive capacity')

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

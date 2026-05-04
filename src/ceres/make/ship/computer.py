from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field, PrivateAttr, field_validator, model_validator

from ceres.gear.computer import ComputerPart
from ceres.gear.software import (
    AnySoftware,
    FixedSoftwarePackage,
    Intellect,
    RatedSoftwarePackage,
    SoftwarePackage,
)

from .base import CeresModel, Note, NoteCategory
from .parts import ShipPart, ShipPartMixin
from .spec import ShipSpec, SpecRow, SpecSection


class Library(FixedSoftwarePackage):
    package: Literal['library'] = 'library'
    label = 'Library'
    _tl = 8
    _bandwidth = 0
    _cost = 0.0


class Manoeuvre(FixedSoftwarePackage):
    package: Literal['manoeuvre'] = 'manoeuvre'
    label = 'Manoeuvre/0'
    _tl = 8
    _bandwidth = 0
    _cost = 0.0


class JumpControl(RatedSoftwarePackage):
    package: Literal['jump_control'] = 'jump_control'
    _label = 'Jump Control'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=5, tl=9, cost=100_000.0),
        2: dict(bandwidth=10, tl=11, cost=200_000.0),
        3: dict(bandwidth=15, tl=12, cost=300_000.0),
        4: dict(bandwidth=20, tl=13, cost=400_000.0),
        5: dict(bandwidth=25, tl=14, cost=500_000.0),
        6: dict(bandwidth=30, tl=15, cost=600_000.0),
    }

    def validate_on_computer(self, computer: ComputerPart) -> None:
        if computer.assembly.tl < self.tl:
            self.error(f'{self.description} requires TL{self.tl}')
            return
        if isinstance(computer, Core):
            self._effective_rating = self.rating
            return
        jcp = computer.jump_control_processing if isinstance(computer, ComputerBase) else computer.processing
        for r in range(self.rating, 0, -1):
            if jcp >= int(self._specs[r]['bandwidth']):
                if r < self.rating:
                    self.warning(f'{computer.description} can only run Jump Control/{r} (degraded from {self.rating})')
                self._effective_rating = r
                return
        self.error(f'{computer.description} cannot run {self.description}')


class AutoRepair(RatedSoftwarePackage):
    package: Literal['auto_repair'] = 'auto_repair'
    _label = 'Auto-Repair'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=10, tl=11, cost=5_000_000.0),
        2: dict(bandwidth=20, tl=12, cost=10_000_000.0),
    }


class FireControl(RatedSoftwarePackage):
    package: Literal['fire_control'] = 'fire_control'
    _label = 'Fire Control'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=5, tl=9, cost=2_000_000.0),
        2: dict(bandwidth=10, tl=11, cost=4_000_000.0),
        3: dict(bandwidth=15, tl=12, cost=6_000_000.0),
        4: dict(bandwidth=20, tl=13, cost=8_000_000.0),
        5: dict(bandwidth=25, tl=14, cost=10_000_000.0),
    }


class AdvancedFireControl(RatedSoftwarePackage):
    package: Literal['advanced_fire_control'] = 'advanced_fire_control'
    _label = 'Advanced Fire Control'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=15, tl=10, cost=12_000_000.0),
        2: dict(bandwidth=25, tl=12, cost=15_000_000.0),
        3: dict(bandwidth=30, tl=14, cost=18_000_000.0),
    }


class AntiHijack(RatedSoftwarePackage):
    package: Literal['anti_hijack'] = 'anti_hijack'
    _label = 'Anti-Hijack'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=2, tl=11, cost=6_000_000.0),
        2: dict(bandwidth=10, tl=12, cost=8_000_000.0),
        3: dict(bandwidth=15, tl=13, cost=10_000_000.0),
    }


class Evade(RatedSoftwarePackage):
    package: Literal['evade'] = 'evade'
    _label = 'Evade'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=10, tl=9, cost=1_000_000.0),
        2: dict(bandwidth=15, tl=11, cost=2_000_000.0),
        3: dict(bandwidth=25, tl=13, cost=3_000_000.0),
    }


class BattleNetwork(RatedSoftwarePackage):
    package: Literal['battle_network'] = 'battle_network'
    _label = 'Battle Network'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=5, tl=12, cost=5_000_000.0),
        2: dict(bandwidth=10, tl=14, cost=10_000_000.0),
    }


class BattleSystem(RatedSoftwarePackage):
    package: Literal['battle_system'] = 'battle_system'
    _label = 'Battle System'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=5, tl=9, cost=18_000_000.0),
        2: dict(bandwidth=10, tl=12, cost=24_000_000.0),
        3: dict(bandwidth=15, tl=15, cost=36_000_000.0),
    }


class BroadSpectrumEW(FixedSoftwarePackage):
    package: Literal['broad_spectrum_ew'] = 'broad_spectrum_ew'
    label = 'Broad Spectrum EW'
    _tl = 13
    _bandwidth = 12
    _cost = 14_000_000.0


class ConsciousIntelligence(RatedSoftwarePackage):
    package: Literal['conscious_intelligence'] = 'conscious_intelligence'
    _label = 'Conscious Intelligence'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=40, tl=16, cost=25_000_000.0),
        2: dict(bandwidth=25, tl=17, cost=20_000_000.0),
        3: dict(bandwidth=10, tl=18, cost=15_000_000.0),
    }


class ElectronicWarfare(RatedSoftwarePackage):
    package: Literal['electronic_warfare'] = 'electronic_warfare'
    _label = 'Electronic Warfare'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=10, tl=10, cost=15_000_000.0),
        2: dict(bandwidth=15, tl=13, cost=18_000_000.0),
        3: dict(bandwidth=20, tl=15, cost=24_000_000.0),
    }


class LaunchSolution(RatedSoftwarePackage):
    package: Literal['launch_solution'] = 'launch_solution'
    _label = 'Launch Solution'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=5, tl=8, cost=10_000_000.0),
        2: dict(bandwidth=10, tl=10, cost=12_000_000.0),
        3: dict(bandwidth=15, tl=12, cost=16_000_000.0),
    }


class PointDefence(RatedSoftwarePackage):
    package: Literal['point_defence'] = 'point_defence'
    _label = 'Point Defence'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(bandwidth=12, tl=9, cost=8_000_000.0),
        2: dict(bandwidth=15, tl=12, cost=12_000_000.0),
    }


class ScreenOptimiser(FixedSoftwarePackage):
    package: Literal['screen_optimiser'] = 'screen_optimiser'
    label = 'Screen Optimiser'
    _tl = 10
    _bandwidth = 10
    _cost = 5_000_000.0


class VirtualCrew(RatedSoftwarePackage):
    package: Literal['virtual_crew'] = 'virtual_crew'
    _label = 'Virtual Crew'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: dict(bandwidth=5, tl=10, cost=1_000_000.0),
        1: dict(bandwidth=10, tl=13, cost=5_000_000.0),
        2: dict(bandwidth=15, tl=15, cost=10_000_000.0),
    }


class VirtualGunner(RatedSoftwarePackage):
    package: Literal['virtual_gunner'] = 'virtual_gunner'
    _label = 'Virtual Gunner'
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: dict(bandwidth=5, tl=9, cost=1_000_000.0),
        1: dict(bandwidth=10, tl=12, cost=5_000_000.0),
        2: dict(bandwidth=15, tl=15, cost=10_000_000.0),
    }


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

ShipSoftware = Annotated[
    AnySoftware
    # Ship software (HG)
    | Library
    | Manoeuvre
    | JumpControl
    | AutoRepair
    | FireControl
    | AdvancedFireControl
    | AntiHijack
    | Evade
    | BattleNetwork
    | BattleSystem
    | BroadSpectrumEW
    | ConsciousIntelligence
    | ElectronicWarfare
    | LaunchSolution
    | PointDefence
    | ScreenOptimiser
    | VirtualCrew
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

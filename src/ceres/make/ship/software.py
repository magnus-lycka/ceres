from typing import TYPE_CHECKING, Annotated, ClassVar, Literal

from pydantic import Field

from ceres.gear.software import AnySoftware, FixedSoftwarePackage, RatedSoftwarePackage

if TYPE_CHECKING:
    from ceres.gear.computer import ComputerPart


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
        from .computer import ComputerBase, _Core  # local import to avoid circular dependency

        if computer.assembly.tl < self.tl:
            self.error(f'{self.description} requires TL{self.tl}')
            return
        if isinstance(computer, _Core):
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

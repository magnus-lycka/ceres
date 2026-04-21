import math
from typing import ClassVar, Literal

from .base import Note, NoteCategory
from .computer import JumpControl, SoftwarePackage
from .parts import (
    CustomisableShipPart,
    EnergyEfficient,
    EnergyInefficient,
    IncreasedSize,
    Modification,
    ShipPart,
    SizeReduction,
)
from .spec import ShipSpec, SpecSection

LimitedRange = Modification(
    name='Limited Range',
    disadvantage=1,
    info_notes=('This manoeuvre drive only functions within the 100-diameter limit',),
)

OrbitalRange = Modification(
    name='Orbital Range',
    disadvantage=2,
    info_notes=('Operational range increased to orbital distances',),
)

DecreasedFuel = Modification(
    name='Decreased Fuel',
    advantage=1,
    fuel_delta_percent=-0.05,
)


class RDrive(ShipPart):
    _specs: ClassVar[dict[int, dict[str, float | int]]] = {
        0: dict(tons_percent=0.01, minimum_tl=7),
        1: dict(tons_percent=0.02, minimum_tl=7),
        2: dict(tons_percent=0.04, minimum_tl=7),
        3: dict(tons_percent=0.06, minimum_tl=7),
        4: dict(tons_percent=0.08, minimum_tl=8),
        5: dict(tons_percent=0.10, minimum_tl=8),
        6: dict(tons_percent=0.12, minimum_tl=8),
        7: dict(tons_percent=0.14, minimum_tl=9),
        8: dict(tons_percent=0.16, minimum_tl=9),
        9: dict(tons_percent=0.18, minimum_tl=9),
        10: dict(tons_percent=0.20, minimum_tl=10),
        11: dict(tons_percent=0.22, minimum_tl=10),
        12: dict(tons_percent=0.24, minimum_tl=10),
        13: dict(tons_percent=0.26, minimum_tl=11),
        14: dict(tons_percent=0.28, minimum_tl=11),
        15: dict(tons_percent=0.30, minimum_tl=11),
        16: dict(tons_percent=0.32, minimum_tl=12),
    }
    level: int
    high_burn_thruster: bool = False

    def __init__(self, level: int | None = None, /, **data):
        if level is not None and 'level' not in data:
            data['level'] = level
        super().__init__(**data)

    @property
    def minimum_tl(self) -> int:
        return int(self._specs[self.level]['minimum_tl'])

    def build_item(self) -> str | None:
        if self.high_burn_thruster:
            return f'High-Burn Thruster, Thrust {self.level}'
        return f'R-Drive Thrust {self.level}'

    def bulkhead_label(self) -> str:
        return 'R-Drive'

    def compute_tons(self) -> float:
        tons_percent = float(self._specs[self.level]['tons_percent'])
        return self.ship.displacement * tons_percent

    def compute_cost(self) -> float:
        return self.compute_tons() * 200_000.0

    def compute_power(self) -> float:
        return 0.0

    def build_notes(self) -> list:
        if not self.high_burn_thruster:
            return []
        return [Note(category=NoteCategory.INFO, message='No inertial compensation above manoeuvre-drive thrust')]

    def validate_tl(self) -> None:
        if self.level not in self._specs:
            self.error(f'Unsupported reaction drive level {self.level}')
            return
        super().validate_tl()


class MDrive(CustomisableShipPart):
    level: int
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        0: dict(minimum_tl=9, tons_percent=0.005),
        1: dict(minimum_tl=9, tons_percent=0.01),
        2: dict(minimum_tl=10, tons_percent=0.02),
        3: dict(minimum_tl=10, tons_percent=0.03),
        4: dict(minimum_tl=11, tons_percent=0.04),
        5: dict(minimum_tl=11, tons_percent=0.05),
        6: dict(minimum_tl=12, tons_percent=0.06),
        7: dict(minimum_tl=13, tons_percent=0.07),
        8: dict(minimum_tl=14, tons_percent=0.08),
        9: dict(minimum_tl=15, tons_percent=0.09),
        10: dict(minimum_tl=16, tons_percent=0.10),
        11: dict(minimum_tl=17, tons_percent=0.11),
    }
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            EnergyEfficient.name,
            EnergyInefficient.name,
            IncreasedSize.name,
            LimitedRange.name,
            OrbitalRange.name,
            SizeReduction.name,
        }
    )

    def __init__(self, level: int | None = None, /, **data):
        if level is not None and 'level' not in data:
            data['level'] = level
        super().__init__(**data)

    @property
    def minimum_tl(self) -> int:
        return int(self._specs[self.level]['minimum_tl'])

    def build_item(self) -> str | None:
        return f'M-Drive {self.level}'

    def bulkhead_label(self) -> str:
        return 'M-Drive'

    def _base_tons(self) -> float:
        tons_percent = float(self._specs[self.level]['tons_percent'])
        return self.ship.displacement * tons_percent

    @property
    def effective_tl(self) -> int:
        return self.minimum_tl + (0 if self.customisation is None else self.customisation.tl_delta)

    def validate_tl(self) -> None:
        if self.level not in self._specs:
            self.error(f'Unsupported M-Drive level {self.level}')
            return
        if self.ship_tl < self.effective_tl:
            self.error(f'Requires TL{self.effective_tl}, ship is TL{self.ship_tl}')

    def compute_tons(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return self._base_tons() * multiplier

    def compute_cost(self) -> float:
        cost = self._base_tons() * 2_000_000
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return cost * multiplier

    def compute_power(self) -> float:
        power = float(math.ceil(0.1 * self.ship.displacement * self.level))
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return power * multiplier


class JDrive(CustomisableShipPart):
    level: int
    _specs: ClassVar[dict[int, dict[str, int | float]]] = {
        1: dict(minimum_tl=9, tons_percent=0.025),
        2: dict(minimum_tl=11, tons_percent=0.05),
        3: dict(minimum_tl=12, tons_percent=0.075),
        4: dict(minimum_tl=13, tons_percent=0.10),
        5: dict(minimum_tl=14, tons_percent=0.125),
        6: dict(minimum_tl=15, tons_percent=0.15),
        7: dict(minimum_tl=16, tons_percent=0.175),
        8: dict(minimum_tl=17, tons_percent=0.20),
        9: dict(minimum_tl=18, tons_percent=0.225),
    }
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            DecreasedFuel.name,
            EnergyEfficient.name,
            SizeReduction.name,
        }
    )

    def __init__(self, level: int | None = None, /, **data):
        if level is not None and 'level' not in data:
            data['level'] = level
        super().__init__(**data)

    @property
    def minimum_tl(self) -> int:
        return int(self._specs[self.level]['minimum_tl'])

    def build_item(self) -> str | None:
        return f'Jump {self.level}'

    def bulkhead_label(self) -> str:
        return 'Jump Drive'

    @property
    def parsecs(self) -> int:
        return self.level

    @property
    def effective_tl(self) -> int:
        return self.minimum_tl + (0 if self.customisation is None else self.customisation.tl_delta)

    def validate_tl(self) -> None:
        if self.level not in self._specs:
            self.error(f'Unsupported J-Drive level {self.level}')
            return
        if self.ship_tl < self.effective_tl:
            self.error(f'Requires TL{self.effective_tl}, ship is TL{self.ship_tl}')

    def compute_tons(self) -> float:
        tons_percent = float(self._specs[self.level]['tons_percent'])
        base_tons = self.ship.displacement * tons_percent + 5
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return base_tons * multiplier

    def compute_cost(self) -> float:
        tons_percent = float(self._specs[self.level]['tons_percent'])
        base_cost = (self.ship.displacement * tons_percent + 5) * 1_500_000
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return base_cost * multiplier

    def compute_power(self) -> float:
        base_power = float(math.ceil(0.1 * self.ship.displacement * self.level))
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return base_power * multiplier


class DriveSection(ShipPart):
    m_drive: MDrive | None = None
    r_drive: RDrive | None = None
    j_drive: JDrive | None = None

    def _all_parts(self) -> list[ShipPart]:
        return [part for part in [self.m_drive, self.r_drive, self.j_drive] if part is not None]

    def validate_jump_control(self, software_packages: dict[type[SoftwarePackage], SoftwarePackage]) -> None:
        if self.j_drive is None:
            return
        jump_control = software_packages.get(JumpControl)
        if not isinstance(jump_control, JumpControl):
            self.j_drive.warning('No Jump Control software')
            return
        if jump_control.rating < self.j_drive.level:
            self.j_drive.warning(f'Limited to Jump {jump_control.rating} by control software')

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.j_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.JUMP, self.j_drive))
        if self.r_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.PROPULSION, self.r_drive))
        if self.m_drive is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.PROPULSION, self.m_drive))


class _FusionPlant(CustomisableShipPart):
    minimum_tl: ClassVar[int]
    power_per_ton: ClassVar[int]
    cost_per_ton: ClassVar[int]
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            IncreasedSize.name,
            SizeReduction.name,
            EnergyInefficient.name,
        }
    )
    output: int

    def build_item(self) -> str | None:
        return f'Fusion (TL {self.minimum_tl})'

    def bulkhead_label(self) -> str:
        return 'Power Plant'

    @property
    def fusion_tl(self) -> int:
        return self.minimum_tl

    @property
    def effective_tl(self):
        return self.minimum_tl + (0 if self.customisation is None else self.customisation.tl_delta)

    def validate_tl(self) -> None:
        if self.ship_tl < self.effective_tl:
            self.error(f'Requires TL{self.effective_tl}, ship is TL{self.ship_tl}')

    def compute_tons(self) -> float:
        tons = self.output / self.power_per_ton
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return tons * multiplier

    def compute_cost(self) -> float:
        cost = (self.output / self.power_per_ton) * self.cost_per_ton
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return cost * multiplier


class FusionPlantTL8(_FusionPlant):
    plant_type: Literal['fusion_tl8'] = 'fusion_tl8'
    minimum_tl = 8
    power_per_ton = 10
    cost_per_ton = 500_000


class FusionPlantTL12(_FusionPlant):
    plant_type: Literal['fusion_tl12'] = 'fusion_tl12'
    minimum_tl = 12
    power_per_ton = 15
    cost_per_ton = 1_000_000


class FusionPlantTL15(_FusionPlant):
    plant_type: Literal['fusion_tl15'] = 'fusion_tl15'
    minimum_tl = 15
    power_per_ton = 20
    cost_per_ton = 2_000_000


class EmergencyPowerSystem(ShipPart):
    @classmethod
    def from_fusion_plant(cls, plant: _FusionPlant) -> EmergencyPowerSystem:
        return cls()

    def build_item(self) -> str | None:
        return 'Emergency Power System'

    @property
    def source_plant(self) -> _FusionPlant:
        power_section = getattr(self.ship, 'power', None)
        plant = None if power_section is None else power_section.fusion_plant
        if plant is None:
            raise RuntimeError('EmergencyPowerSystem requires a fusion plant')
        return plant

    def compute_tons(self) -> float:
        return self.source_plant.tons * 0.1

    def compute_cost(self) -> float:
        return self.source_plant.cost * 0.1


class PowerSection(ShipPart):
    fusion_plant: FusionPlantTL8 | FusionPlantTL12 | FusionPlantTL15 | None = None
    emergency_power_system: EmergencyPowerSystem | None = None

    def _all_parts(self) -> list[ShipPart]:
        return [part for part in [self.fusion_plant, self.emergency_power_system] if part is not None]

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        if self.fusion_plant is not None:
            spec.add_row(
                ship._spec_row_for_part(
                    SpecSection.POWER,
                    self.fusion_plant,
                    power=float(self.fusion_plant.output),
                    emphasize_power=True,
                )
            )
        if self.emergency_power_system is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.POWER, self.emergency_power_system))

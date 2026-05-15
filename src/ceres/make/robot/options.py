"""Robot option classes — slotted and zero-slot options for Phase 3.

Rule sources:
  refs/robot/21_cleaning_options.md     (DomesticCleaningEquipment)
  refs/robot/22_communications_options.md (RoboticDroneController)
  refs/robot/07_chassis_options.md      (DecreasedResiliency)
  refs/robot/29_storage_compartment.md  (StorageCompartment, ExternalPower)
  refs/robot/31_neural_activity_sensor.md (ReconSensor)
"""

from math import floor
from typing import Any

from .chassis import chassis_entry
from .parts import RobotBase, RobotPart
from .skills import SkillGrant

_CLEANING_TABLE: dict[str, dict[str, int | float]] = {
    'small': {'slots': 1, 'cost': 100.0},
    'medium': {'slots': 4, 'cost': 1000.0},
    'large': {'slots': 8, 'cost': 5000.0},
}

_RECON_SENSOR_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 7, 'slots': 2, 'level': 1, 'cost': 1000.0},
    'improved': {'tl': 8, 'slots': 1, 'level': 1, 'cost': 100.0},
    'enhanced': {'tl': 10, 'slots': 1, 'level': 2, 'cost': 10000.0},
    'advanced': {'tl': 12, 'slots': 1, 'level': 3, 'cost': 20000.0},
}

_DRONE_CONTROLLER_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 7, 'slots': 2, 'cost': 2000.0},
    'improved': {'tl': 9, 'slots': 1, 'cost': 10000.0},
    'enhanced': {'tl': 10, 'slots': 1, 'cost': 20000.0},
    'advanced': {'tl': 11, 'slots': 1, 'cost': 50000.0},
}


class StorageCompartment(RobotPart):
    """refs/robot/29_storage_compartment.md — Cr50/slot, TL6."""

    slots_count: int
    tl: int = 6

    @property
    def slots(self) -> int:
        return self.slots_count

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', float(self.slots_count) * 50.0)

    def build_item(self) -> str | None:
        return f'Storage Compartment ({self.slots_count} Slots)'


class DomesticCleaningEquipment(RobotPart):
    """refs/robot/21_cleaning_options.md."""

    size: str
    tl: int = 5

    @property
    def slots(self) -> int:
        return int(_CLEANING_TABLE[self.size]['slots'])

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', float(_CLEANING_TABLE[self.size]['cost']))

    def build_item(self) -> str | None:
        return f'Domestic Cleaning Equipment ({self.size})'


class ReconSensor(RobotPart):
    """refs/robot/31_neural_activity_sensor.md — Recon Sensor table.

    Skill grants are hardware-based: NOT modified by robot INT DM.
    """

    quality: str = 'improved'

    @property
    def slots(self) -> int:
        return int(_RECON_SENSOR_TABLE[self.quality]['slots'])

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        level = int(_RECON_SENSOR_TABLE[self.quality]['level'])
        return (SkillGrant('Recon', level),)

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _RECON_SENSOR_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def build_item(self) -> str | None:
        return f'Recon Sensor ({self.quality})'


class ExternalPower(RobotPart):
    """refs/robot/29_storage_compartment.md — External Power.

    Slots = floor(5% × base_slots); Cost = Cr100 × base_slots.
    Requires binding to compute (both depend on robot size).
    """

    tl: int = 9

    @property
    def slots(self) -> int:
        if self._assembly is None:
            return 0
        base = chassis_entry(self.assembly.size).base_slots
        return floor(0.05 * base)

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        base = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', float(base) * 100.0)

    def build_item(self) -> str | None:
        return 'External Power'


class RoboticDroneController(RobotPart):
    """refs/robot/22_communications_options.md — Robotic Drone Controller table."""

    quality: str = 'basic'

    @property
    def slots(self) -> int:
        return int(_DRONE_CONTROLLER_TABLE[self.quality]['slots'])

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _DRONE_CONTROLLER_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def build_item(self) -> str | None:
        return f'Robotic Drone Controller ({self.quality})'


class DecreasedResiliency(RobotPart):
    """refs/robot/07_chassis_options.md — Decreased Resiliency.

    Chassis modification: reduces hits, saves cost. Not listed in options display.
    Cost saving = hit_reduction × Cr50 × locomotion_cost_multiplier.
    """

    hit_reduction: int

    @property
    def hits_delta(self) -> int:
        return -self.hit_reduction

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        multiplier = assembly.locomotion.cost_multiplier
        object.__setattr__(self, 'cost', -(self.hit_reduction * 50.0 * multiplier))


__all__ = [
    'StorageCompartment',
    'DomesticCleaningEquipment',
    'ReconSensor',
    'ExternalPower',
    'RoboticDroneController',
    'DecreasedResiliency',
]

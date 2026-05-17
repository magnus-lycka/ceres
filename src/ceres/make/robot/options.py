"""Robot option classes.

Rule sources:
  refs/robot/10_default_suite.md        (default suite items)
  refs/robot/14_encryption_module.md    (RobotTransceiver, VideoScreen)
  refs/robot/21_cleaning_options.md     (DomesticCleaningEquipment)
  refs/robot/22_communications_options.md (RoboticDroneController)
  refs/robot/23_satellite_uplink.md     (SwarmController)
  refs/robot/07_chassis_options.md      (DecreasedResiliency)
  refs/robot/08_locomotion_modifications.md (VehicleSpeedModification)
  refs/robot/09_manipulators.md         (AdditionalManipulator)
  refs/robot/18_geiger_counter.md       (LightIntensifierSensor, OlfactorySensor, ThermalSensor)
  refs/robot/29_storage_compartment.md  (StorageCompartment, ExternalPower)
  refs/robot/31_neural_activity_sensor.md (ReconSensor)
  refs/robot/32_navigation_system.md    (NavigationSystem)
  refs/robot/42_avatars.md              (AvatarController)
"""

from math import ceil
from typing import Any

from ceres.gear.comm import RadioTransceiverPart

from .chassis import Trait, chassis_entry
from .parts import RobotBase, RobotPart, RobotPartMixin
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


_STORAGE_COST_PER_SLOT: dict[str, float] = {
    'standard': 50.0,
    'refrigerated': 100.0,
    'hazardous': 500.0,
}


class StorageCompartment(RobotPart):
    """refs/robot/29_storage_compartment.md — TL6; Cr50/slot standard, Cr100/slot refrigerated, Cr500/slot hazardous."""

    slots_count: int
    storage_type: str = 'standard'
    tl: int = 6

    @property
    def slots(self) -> int:
        return self.slots_count

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        cost_per_slot = _STORAGE_COST_PER_SLOT.get(self.storage_type, 50.0)
        object.__setattr__(self, 'cost', float(self.slots_count) * cost_per_slot)

    def build_item(self) -> str | None:
        if self.storage_type == 'standard':
            return f'Storage Compartment ({self.slots_count} Slots)'
        elif self.storage_type == 'hazardous':
            return f'Storage Compartment ({self.slots_count} Slots hazardous material)'
        return f'Storage Compartment ({self.slots_count} Slots {self.storage_type})'


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

    Slots = ceil(5% × base_slots); Cost = Cr100 × base_slots.
    Requires binding to compute (both depend on robot size).
    """

    tl: int = 9

    @property
    def slots(self) -> int:
        if self._assembly is None:
            return 0
        base = chassis_entry(self.assembly.size).base_slots
        return ceil(0.05 * base)

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


_NAVIGATION_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 8, 'slots': 2, 'level': 1, 'cost': 2000.0},
}

_AGRICULTURAL_TABLE: dict[str, dict[str, int | float]] = {
    'small': {'tl': 5, 'slots': 2, 'cost': 500.0},
    'medium': {'tl': 5, 'slots': 4, 'cost': 1000.0},
    'large': {'tl': 5, 'slots': 8, 'cost': 5000.0},
}

_LIGHT_INTENSIFIER_TABLE: dict[str, tuple[int, float, str | None]] = {
    'basic': (7, 500.0, None),
    'advanced': (9, 1250.0, 'IR Vision'),
}

_OLFACTORY_TABLE: dict[str, tuple[int, float, str | None]] = {
    'basic': (8, 1000.0, None),
    'improved': (10, 3500.0, 'Heightened Senses'),
    'advanced': (12, 10000.0, None),
}


class NavigationSystem(RobotPart):
    """refs/robot/32_navigation_system.md — Navigation System table."""

    quality: str = 'basic'

    @property
    def slots(self) -> int:
        return int(_NAVIGATION_TABLE[self.quality]['slots'])

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        level = int(_NAVIGATION_TABLE[self.quality]['level'])
        return (SkillGrant('Navigation', level),)

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _NAVIGATION_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def build_item(self) -> str | None:
        return f'Navigation System ({self.quality})'


class AgriculturalEquipment(RobotPart):
    """refs/robot/105_utility_robots.md — Agricultural Equipment."""

    size: str = 'medium'

    @property
    def slots(self) -> int:
        return int(_AGRICULTURAL_TABLE[self.size]['slots'])

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _AGRICULTURAL_TABLE[self.size]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def build_item(self) -> str | None:
        return f'Agricultural Equipment ({self.size})'


class LightIntensifierSensor(RobotPart):
    """refs/robot/18_geiger_counter.md — Light Intensifier Sensor."""

    quality: str = 'basic'

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        _tl, _cost, trait_name = _LIGHT_INTENSIFIER_TABLE[self.quality]
        if trait_name:
            return (Trait(trait_name),)
        return ()

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        tl, cost, _trait = _LIGHT_INTENSIFIER_TABLE[self.quality]
        object.__setattr__(self, 'tl', tl)
        object.__setattr__(self, 'cost', cost)

    def build_item(self) -> str | None:
        return f'Light Intensifier Sensor ({self.quality})'


class OlfactorySensor(RobotPart):
    """refs/robot/18_geiger_counter.md — Olfactory Sensor."""

    quality: str = 'basic'

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        _tl, _cost, trait_name = _OLFACTORY_TABLE[self.quality]
        if trait_name:
            return (Trait(trait_name),)
        return ()

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        tl, cost, _trait = _OLFACTORY_TABLE[self.quality]
        object.__setattr__(self, 'tl', tl)
        object.__setattr__(self, 'cost', cost)

    def build_item(self) -> str | None:
        return f'Olfactory Sensor ({self.quality})'


class ThermalSensor(RobotPart):
    """refs/robot/18_geiger_counter.md — Thermal Sensor, TL6, IR Vision, Cr500."""

    tl: int = 6

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        return (Trait('IR Vision'),)

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 500.0)

    def build_item(self) -> str | None:
        return 'Thermal Sensor'


class VehicleSpeedModification(RobotPart):
    """refs/robot/08_locomotion_modifications.md — Vehicle Speed Movement.

    Slots = ceil(25% × base_slots). Cost = Base Chassis Cost.
    Replaces the locomotion's Flyer (idle) trait with the vehicle speed band trait.
    Reduces endurance by ×4 when operating at vehicle speed.
    """

    @property
    def slots(self) -> int:
        if self._assembly is None:
            return 0
        base = chassis_entry(self.assembly.size).base_slots
        return ceil(0.25 * base)

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        from .locomotion import GravLocomotion

        if self._assembly is not None and isinstance(self.assembly.locomotion, GravLocomotion):
            return (Trait('Flyer', 'high'),)
        return ()

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        bcc = chassis_entry(assembly.size).basic_cost * assembly.locomotion.cost_multiplier
        object.__setattr__(self, 'cost', bcc)

    def build_item(self) -> str | None:
        return None  # locomotion modification — not listed in Options row


_AVATAR_CONTROLLER_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 11, 'slots': 2, 'cost': 50000.0},
    'improved': {'tl': 13, 'slots': 1, 'cost': 200000.0},
    'enhanced': {'tl': 14, 'slots': 1, 'cost': 500000.0},
    'advanced': {'tl': 16, 'slots': 1, 'cost': 1000000.0},
}

_SWARM_CONTROLLER_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 8, 'slots': 3, 'cost': 10000.0},
    'improved': {'tl': 10, 'slots': 2, 'cost': 20000.0},
    'enhanced': {'tl': 12, 'slots': 1, 'cost': 50000.0},
    'advanced': {'tl': 14, 'slots': 1, 'cost': 100000.0},
}


class AvatarController(RobotPart):
    """refs/robot/42_avatars.md — Avatar Controller table."""

    quality: str = 'basic'

    @property
    def slots(self) -> int:
        return int(_AVATAR_CONTROLLER_TABLE[self.quality]['slots'])

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _AVATAR_CONTROLLER_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def build_item(self) -> str | None:
        return f'Avatar Controller ({self.quality})'


class SwarmController(RobotPart):
    """refs/robot/23_satellite_uplink.md — Swarm Controller table."""

    quality: str = 'enhanced'

    @property
    def slots(self) -> int:
        return int(_SWARM_CONTROLLER_TABLE[self.quality]['slots'])

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _SWARM_CONTROLLER_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def build_item(self) -> str | None:
        return f'Swarm Controller ({self.quality})'


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


# ── Default suite item classes ────────────────────────────────────────────────
# Each class is zero-cost; cost is included in the base chassis cost (BCC).
# refs/robot/10_default_suite.md


class VisualSpectrumSensor(RobotPart):
    """refs/robot/10_default_suite.md — Visual Spectrum Sensor, TL8, zero-slot."""

    tl: int = 8

    def build_item(self) -> str | None:
        return 'Visual Spectrum Sensor'


class VoderSpeaker(RobotPart):
    """refs/robot/10_default_suite.md — Voder Speaker, TL8, zero-slot."""

    tl: int = 8

    def build_item(self) -> str | None:
        return 'Voder Speaker'


class AuditorySensor(RobotPart):
    """refs/robot/10_default_suite.md — Auditory Sensor, TL8, zero-slot."""

    tl: int = 8

    def build_item(self) -> str | None:
        return 'Auditory Sensor'


class WirelessDataLink(RobotPart):
    """refs/robot/10_default_suite.md — Wireless Data Link, TL8, zero-slot."""

    tl: int = 8

    def build_item(self) -> str | None:
        return 'Wireless Data Link'


class DroneInterface(RobotPart):
    """refs/robot/10_default_suite.md — Drone Interface, TL6, zero-slot.

    Free default-suite substitution; cost source unknown, always Cr0.
    """

    tl: int = 6

    def build_item(self) -> str | None:
        return 'Drone Interface'


# Robot Handbook zero-slot transceiver table (refs/robot/14_encryption_module.md).
# These costs are robot-installation specific and differ from CSC handheld prices.
_ROBOT_TRANSCEIVER_TABLE: dict[tuple[str, int], dict[str, int | float]] = {
    ('basic', 5): {'tl': 7, 'cost': 250.0},
    ('improved', 5): {'tl': 8, 'cost': 100.0},
    ('improved', 50): {'tl': 8, 'cost': 500.0},
    ('enhanced', 50): {'tl': 10, 'cost': 250.0},
    ('advanced', 50): {'tl': 13, 'cost': 100.0},
    ('improved', 500): {'tl': 9, 'cost': 1000.0},
    ('enhanced', 500): {'tl': 11, 'cost': 500.0},
    ('advanced', 500): {'tl': 14, 'cost': 250.0},
    ('improved', 5000): {'tl': 9, 'cost': 5000.0},
    ('enhanced', 5000): {'tl': 12, 'cost': 1000.0},
    ('advanced', 5000): {'tl': 15, 'cost': 500.0},
}

_VIDEO_SCREEN_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 7, 'cost': 200.0},
    'improved': {'tl': 8, 'cost': 500.0},
    'advanced': {'tl': 10, 'cost': 2000.0},
}


class VideoScreen(RobotPart):
    """refs/robot/14_encryption_module.md — Video Screen, zero-slot.

    Quality: basic (TL7, Cr200) / improved (TL8, Cr500) / advanced (TL10, Cr2000).
    Set is_default_suite=True (via default_suite()) to include at no cost in BCC.
    """

    quality: str = 'basic'
    is_default_suite: bool = False

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _VIDEO_SCREEN_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        if not self.is_default_suite:
            object.__setattr__(self, 'cost', float(entry['cost']))

    def build_item(self) -> str | None:
        return f'Video Screen ({self.quality})'


class RobotTransceiver(RadioTransceiverPart, RobotPartMixin):
    """Zero-slot radio transceiver for robot installation.

    refs/robot/14_encryption_module.md — Robot Handbook zero-slot table.
    TL and cost are robot-installation specific (not CSC handheld equipment prices).
    Set is_default_suite=True (via default_suite()) to include at no cost in BCC.
    """

    quality: str = 'improved'
    is_default_suite: bool = False

    @property
    def slots(self) -> int:
        return 0

    @property
    def assembly(self) -> RobotBase:
        a = self._assembly
        if a is None:
            raise RuntimeError(f'{type(self).__name__} not bound to an Assembly')
        if not isinstance(a, RobotBase):
            raise RuntimeError(f'{type(self).__name__} bound to unexpected type {type(a).__name__}')
        return a

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _ROBOT_TRANSCEIVER_TABLE[(self.quality, self.range_km)]
        object.__setattr__(self, 'tl', int(entry['tl']))
        if not self.is_default_suite:
            object.__setattr__(self, 'cost', float(entry['cost']))

    def build_item(self) -> str | None:
        return f'Transceiver {self.range_km:,}km ({self.quality})'


def default_suite(
    see: bool = True,
    speak: bool = True,
    hear: bool = True,
    wireless: bool = True,
    improved_transceiver: bool = True,
    drone: bool = False,
    basic_transceiver: bool = False,
    screen: bool = False,
) -> list[RobotPartMixin]:
    """Return the five standard default suite items (all zero-cost, included in BCC).

    refs/robot/10_default_suite.md — substitution rules.
    At most five of the eight flags may be True; validation error otherwise.
    Flags: see (Visual Spectrum Sensor), speak (Voder Speaker), hear (Auditory
    Sensor), wireless (Wireless Data Link), improved_transceiver (Transceiver 5km
    improved), drone (Drone Interface), basic_transceiver (Transceiver 5km basic),
    screen (Video Screen basic).
    """
    flags = [see, speak, hear, wireless, improved_transceiver, drone, basic_transceiver, screen]
    if sum(flags) > 5:
        raise ValueError(f'default_suite allows at most 5 items; got {sum(flags)}')
    items: list[RobotPartMixin] = []
    if see:
        items.append(VisualSpectrumSensor())
    if speak:
        items.append(VoderSpeaker())
    if hear:
        items.append(AuditorySensor())
    if wireless:
        items.append(WirelessDataLink())
    if improved_transceiver:
        items.append(RobotTransceiver(range_km=5, quality='improved', is_default_suite=True))
    if drone:
        items.append(DroneInterface())
    if basic_transceiver:
        items.append(RobotTransceiver(range_km=5, quality='basic', is_default_suite=True))
    if screen:
        items.append(VideoScreen(quality='basic', is_default_suite=True))
    return items


__all__ = [
    'VisualSpectrumSensor',
    'VoderSpeaker',
    'AuditorySensor',
    'WirelessDataLink',
    'DroneInterface',
    'VideoScreen',
    'RobotTransceiver',
    'default_suite',
    'StorageCompartment',
    'DomesticCleaningEquipment',
    'ReconSensor',
    'ExternalPower',
    'RoboticDroneController',
    'AvatarController',
    'SwarmController',
    'DecreasedResiliency',
    'NavigationSystem',
    'AgriculturalEquipment',
    'LightIntensifierSensor',
    'OlfactorySensor',
    'ThermalSensor',
    'VehicleSpeedModification',
]

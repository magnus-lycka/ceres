"""Robot option classes.

Rule sources:
  refs/robot/10_default_suite.md        (default suite items)
  refs/robot/11_zero_slot_options.md    (CamouflageVisual)
  refs/robot/12_camouflage_audible_concealment.md (CamouflageAudible, CamouflageOlfactory)
  refs/robot/13_solar_coating.md        (VacuumEnvironmentProtection)
  refs/robot/14_encryption_module.md    (RobotTransceiver, VideoScreen, EncryptionModule)
  refs/robot/15_voder_speaker.md        (GeckoGrippers, VoderSpeaker broad spectrum, InjectorNeedle)
  refs/robot/16_laser_designator.md     (ParasiticLink, SelfMaintenanceEnhancement)
  refs/robot/17_stinger.md              (AuditorySensor broad spectrum, EnvironmentProcessor)
  refs/robot/21_cleaning_options.md     (DomesticCleaningEquipment)
  refs/robot/22_communications_options.md (RoboticDroneController)
  refs/robot/23_satellite_uplink.md     (SwarmController)
  refs/robot/07_chassis_options.md      (DecreasedResiliency, IncreasedArmour, Efficiency)
  refs/robot/08_locomotion_modifications.md (VehicleSpeedModification, AgilityEnhancement, SecondaryLocomotion)
  refs/robot/09_manipulators.md         (AdditionalManipulator)
  refs/robot/18_geiger_counter.md       (LightIntensifierSensor, OlfactorySensor, PrisSensor, ThermalSensor)
  refs/robot/19_slot_cost_options.md    (ActiveCamouflage)
  refs/robot/20_radiation_environment_protection.md (RadiationEnvironmentProtection)
  refs/robot/27_autobar.md              (Autobar)
  refs/robot/29_storage_compartment.md  (StorageCompartment, ExternalPower)
  refs/robot/31_neural_activity_sensor.md (ReconSensor)
  refs/robot/32_navigation_system.md    (NavigationSystem)
  refs/robot/42_avatars.md              (AvatarController, AvatarReceiver)
"""

from math import ceil
from typing import Any

from ceres.gear.comm import RadioTransceiverPart

from .chassis import Trait, chassis_entry
from .locomotion import LocomotionUnion
from .parts import RobotBase, RobotPart, RobotPartMixin

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

    def item_description(self) -> str:
        if self.storage_type == 'standard':
            return f'Storage Compartment ({self.slots_count} Slots)'
        if self.storage_type == 'hazardous':
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

    def item_description(self) -> str:
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
    def skill_grants(self) -> dict[str, int]:
        level = int(_RECON_SENSOR_TABLE[self.quality]['level'])
        return {'Recon': level}

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _RECON_SENSOR_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def item_description(self) -> str:
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

    def item_description(self) -> str:
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

    def item_description(self) -> str:
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
    def skill_grants(self) -> dict[str, int]:
        level = int(_NAVIGATION_TABLE[self.quality]['level'])
        return {'Navigation': level}

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _NAVIGATION_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def item_description(self) -> str:
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

    def item_description(self) -> str:
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

    def item_description(self) -> str:
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

    def item_description(self) -> str:
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

    def item_description(self) -> str:
        return 'Thermal Sensor'


class PrisSensor(RobotPart):
    """refs/robot/18_geiger_counter.md — PRIS Sensor, TL12, zero-slot, Cr2000, IR/UV Vision."""

    tl: int = 12

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        return (Trait('IR/UV Vision'),)

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 2000.0)

    def item_description(self) -> str:
        return 'PRIS Sensor'


class GeckoGrippers(RobotPart):
    """refs/robot/15_voder_speaker.md — Gecko Grippers, TL9, zero-slot, Cr500/base_slot.

    Allows climbing vertical surfaces and adhering to walls/ceilings in 0–1.5G environments.
    Movement is halved while traversing these surfaces.
    """

    tl: int = 9

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        base_slots = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', 500.0 * base_slots)

    def item_description(self) -> str:
        return 'Gecko Grippers'


# Camouflage tables: (tl, detection_dm, cost_per_base_slot)
# refs/robot/11_zero_slot_options.md — Visual Concealment
_CAMOUFLAGE_VISUAL_TABLE: dict[str, tuple[int, int, float]] = {
    'primitive': (1, -1, 1.0),
    'basic': (4, -2, 4.0),
    'improved': (7, -2, 40.0),
    'enhanced': (11, -3, 100.0),
    'advanced': (12, -4, 500.0),
    'superior': (13, -4, 2500.0),
}

# refs/robot/12_camouflage_audible_concealment.md — Audible Concealment
_CAMOUFLAGE_AUDIBLE_TABLE: dict[str, tuple[int, int, float]] = {
    'basic': (5, -1, 5.0),
    'improved': (8, -2, 10.0),
    'advanced': (10, -3, 50.0),
}

# refs/robot/12_camouflage_audible_concealment.md — Olfactory Concealment
_CAMOUFLAGE_OLFACTORY_TABLE: dict[str, tuple[int, int, float]] = {
    'basic': (7, -1, 10.0),
    'improved': (9, -2, 20.0),
    'advanced': (12, -3, 100.0),
}


class CamouflageVisual(RobotPart):
    """refs/robot/11_zero_slot_options.md — Camouflage: Visual Concealment.

    Zero-slot. Cost = cost_per_base_slot × base_slots.
    Detection DM is considered the equivalent of the robot's Stealth skill.
    """

    quality: str = 'enhanced'

    @property
    def skill_grants(self) -> dict[str, int]:
        _tl, dm, _rate = _CAMOUFLAGE_VISUAL_TABLE[self.quality]
        return {'Stealth': abs(dm)}

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        tl, _dm, _rate = _CAMOUFLAGE_VISUAL_TABLE[self.quality]
        object.__setattr__(self, 'tl', tl)

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        _tl, _dm, rate = _CAMOUFLAGE_VISUAL_TABLE[self.quality]
        base_slots = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', float(rate * base_slots))

    def item_description(self) -> str:
        return f'Camouflage: Visual ({self.quality})'


class CamouflageAudible(RobotPart):
    """refs/robot/12_camouflage_audible_concealment.md — Camouflage: Audible Concealment.

    Zero-slot. Cost = cost_per_base_slot × base_slots.
    Negates Heightened Senses when detecting the concealed robot.
    """

    quality: str = 'advanced'

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        tl, _dm, _rate = _CAMOUFLAGE_AUDIBLE_TABLE[self.quality]
        object.__setattr__(self, 'tl', tl)

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        _tl, _dm, rate = _CAMOUFLAGE_AUDIBLE_TABLE[self.quality]
        base_slots = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', float(rate * base_slots))

    def item_description(self) -> str:
        return f'Camouflage: Audible ({self.quality})'


class CamouflageOlfactory(RobotPart):
    """refs/robot/12_camouflage_audible_concealment.md — Camouflage: Olfactory Concealment.

    Zero-slot. Cost = cost_per_base_slot × base_slots.
    Negates Heightened Senses when detecting the concealed robot.
    """

    quality: str = 'advanced'

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        tl, _dm, _rate = _CAMOUFLAGE_OLFACTORY_TABLE[self.quality]
        object.__setattr__(self, 'tl', tl)

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        _tl, _dm, rate = _CAMOUFLAGE_OLFACTORY_TABLE[self.quality]
        base_slots = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', float(rate * base_slots))

    def item_description(self) -> str:
        return f'Camouflage: Olfactory ({self.quality})'


_AUTOCHEF_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 9, 'slots': 3, 'cost': 500.0},
    'improved': {'tl': 10, 'slots': 3, 'cost': 2000.0},
    'enhanced': {'tl': 11, 'slots': 3, 'cost': 5000.0},
    'advanced': {'tl': 12, 'slots': 3, 'cost': 10000.0},
}


class Autochef(RobotPart):
    """refs/robot/27_autobar.md — Autochef, food preparation system.

    Quality: basic (TL9, Cr500) / improved (TL10, Cr2000) / enhanced (TL11, Cr5000) / advanced (TL12, Cr10000).
    All variants take 3 Slots. Limits Steward or Profession (chef) skill to the quality level when using
    the robot's internal autochef; the skill cap is a game-mechanic and is not enforced by this model.
    """

    quality: str = 'basic'

    @property
    def slots(self) -> int:
        return int(_AUTOCHEF_TABLE[self.quality]['slots'])

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _AUTOCHEF_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def item_description(self) -> str:
        return f'Autochef ({self.quality})'


class StylistToolkit(RobotPart):
    """refs/robot/32_fire_extinguisher.md — Stylist Toolkit, TL6, 3 Slots, Cr2000.

    Tools for hair styling, nail care, makeup and similar species-specific beauty tasks.
    """

    tl: int = 6

    @property
    def slots(self) -> int:
        return 3

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 2000.0)

    def item_description(self) -> str:
        return 'Stylist Toolkit'


class VehicleSpeedModification(RobotPart):
    """refs/robot/08_locomotion_modifications.md — Vehicle Speed Movement.

    Slots = ceil(25% × base_slots). Cost = Base Chassis Cost.
    Replaces the locomotion's Flyer (idle) trait with the vehicle speed band trait.
    Reduces endurance by ×4 when operating at vehicle speed.
    Cannot be combined with Tactical Speed Enhancement or Tactical Speed Reduction (RHB p.53; RIR-010).
    AgilityEnhancement may coexist: it raises tactical speed and grants Athletics (dex), but does not
    affect the vehicle speed band.
    """

    @property
    def slots(self) -> int:
        if self._assembly is None:
            return 0
        base = chassis_entry(self.assembly.size).base_slots
        return ceil(0.25 * base)

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        if self._assembly is None:
            return ()
        loco = self.assembly.locomotion
        band = loco._vehicle_speed_band
        if band and any(t.name == 'Flyer' for t in loco.locomotion_traits):
            return (Trait('Flyer', band),)
        return ()

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        bcc = chassis_entry(assembly.size).basic_cost * assembly.locomotion.cost_multiplier
        object.__setattr__(self, 'cost', bcc)


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

    def item_description(self) -> str:
        return f'Avatar Controller ({self.quality})'


class AvatarReceiver(RobotPart):
    """refs/robot/42_avatars.md — Avatar Receiver. TL11, 1 slot, Cr10000 flat.

    Acts as a drone interface. Requires Advanced brain or higher.
    """

    tl: int = 11

    @property
    def slots(self) -> int:
        return 1

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 10000.0)

    def item_description(self) -> str:
        return 'Avatar Receiver'


class ActiveCamouflage(RobotPart):
    """refs/robot/19_slot_cost_options.md — Active Camouflage. TL15, 1 slot, Cr10000 per base slot.

    Grants Stealth 4 and the Invisible trait. Only one may be installed.
    """

    tl: int = 15

    @property
    def slots(self) -> int:
        return 1

    @property
    def skill_grants(self) -> dict[str, int]:
        return {'Stealth': 4}

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        return (Trait('Invisible'),)

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        base_slots = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', 10000.0 * base_slots)

    def item_description(self) -> str:
        return 'Active Camouflage'


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

    def item_description(self) -> str:
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

    def item_description(self) -> str:
        return 'Visual Spectrum Sensor'


class VoderSpeaker(RobotPart):
    """refs/robot/15_voder_speaker.md — Voder Speaker.

    Standard: TL8, zero-slot, Cr100 standalone.
    Broad spectrum: TL10, zero-slot, Cr500.
    """

    quality: str = 'standard'
    tl: int = 8

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        if self.quality == 'broad_spectrum':
            object.__setattr__(self, 'tl', 10)
            object.__setattr__(self, 'cost', 500.0)

    def item_description(self) -> str:
        if self.quality == 'broad_spectrum':
            return 'Voder Speaker (broad spectrum)'
        return 'Voder Speaker'


class AuditorySensor(RobotPart):
    """refs/robot/17_stinger.md — Auditory Sensor.

    Standard: TL5/TL8 (default suite context), zero-slot, Cr10 standalone.
    Broad spectrum: TL8, zero-slot, Cr200, grants Heightened Senses trait.
    """

    quality: str = 'standard'
    tl: int = 8

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        if self.quality == 'broad_spectrum':
            return (Trait('Heightened Senses'),)
        return ()

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        if self.quality == 'broad_spectrum':
            object.__setattr__(self, 'cost', 200.0)

    def item_description(self) -> str:
        if self.quality == 'broad_spectrum':
            return 'Auditory Sensor (broad spectrum)'
        return 'Auditory Sensor'


class WirelessDataLink(RobotPart):
    """refs/robot/10_default_suite.md — Wireless Data Link, TL8, zero-slot."""

    tl: int = 8

    def item_description(self) -> str:
        return 'Wireless Data Link'


class DroneInterface(RobotPart):
    """refs/robot/10_default_suite.md — Drone Interface, TL6, zero-slot.

    Free default-suite substitution; cost source unknown, always Cr0.
    """

    tl: int = 6

    def item_description(self) -> str:
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

    def item_description(self) -> str:
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
        return self._robot_assembly()

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _ROBOT_TRANSCEIVER_TABLE[(self.quality, self.range_km)]
        object.__setattr__(self, 'tl', int(entry['tl']))
        if not self.is_default_suite:
            object.__setattr__(self, 'cost', float(entry['cost']))

    def item_description(self) -> str:
        return f'Transceiver {self.range_km:,}km ({self.quality})'


class EncryptionModule(RobotPart):
    """refs/robot/14_encryption_module.md — Encryption Module, TL6, zero-slot, Cr4000."""

    tl: int = 6

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 4000.0)

    def item_description(self) -> str:
        return 'Encryption Module'


class EnvironmentProcessor(RobotPart):
    """refs/robot/17_stinger.md — Environment Processor, TL10, zero-slot, Cr10000, Heightened Senses, Recon 0."""

    tl: int = 10

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        return (Trait('Heightened Senses'),)

    @property
    def skill_grants(self) -> dict[str, int]:
        return {'Recon': 0}

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 10000.0)

    def item_description(self) -> str:
        return 'Environment Processor'


class ParasiticLink(RobotPart):
    """refs/robot/16_laser_designator.md — Parasitic Link, TL10, zero-slot, Cr10000."""

    tl: int = 10

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 10000.0)

    def item_description(self) -> str:
        return 'Parasitic Link'


class InjectorNeedle(RobotPart):
    """refs/robot/15_voder_speaker.md — Injector Needle, TL7, zero-slot, Cr20 each."""

    tl: int = 7

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 20.0)

    def item_description(self) -> str:
        return 'Injector Needle'


_SELF_MAINTENANCE_TABLE: dict[str, tuple[int, float, float]] = {
    'basic': (7, 20000.0, 1.0),
    'improved': (8, 50000.0, 2.0),
}


class SelfMaintenanceEnhancement(RobotPart):
    """refs/robot/16_laser_designator.md — Self-Maintenance Enhancement, cost per base slot."""

    quality: str = 'improved'

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        tl, _rate, _mult = _SELF_MAINTENANCE_TABLE[self.quality]
        object.__setattr__(self, 'tl', tl)

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        _tl, rate, _mult = _SELF_MAINTENANCE_TABLE[self.quality]
        base_slots = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', rate * base_slots)

    @property
    def endurance_multiplier(self) -> float:
        _tl, _rate, mult = _SELF_MAINTENANCE_TABLE[self.quality]
        return mult

    def item_description(self) -> str:
        return f'Self-Maintenance Enhancement ({self.quality})'


class VacuumEnvironmentProtection(RobotPart):
    """refs/robot/13_solar_coating.md — Vacuum Environment Protection, TL7, zero-slot, Cr600 per base slot."""

    tl: int = 7

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        base_slots = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', 600.0 * base_slots)

    def item_description(self) -> str:
        return 'Vacuum Environment Protection'


_MEDIKIT_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 8, 'cost': 1000.0},
    'improved': {'tl': 10, 'cost': 1500.0},
    'enhanced': {'tl': 12, 'cost': 5000.0},
    'advanced': {'tl': 14, 'cost': 10000.0},
}

_SOLAR_COATING_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 6, 'cost_per_base_slot': 500.0},
    'improved': {'tl': 8, 'cost_per_base_slot': 100.0},
    'enhanced': {'tl': 10, 'cost_per_base_slot': 200.0},
    'advanced': {'tl': 12, 'cost_per_base_slot': 500.0},
}

_SCIENTIFIC_TOOLKIT_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 5, 'slots': 4, 'cost': 2000.0},
    'improved': {'tl': 8, 'slots': 3, 'cost': 4000.0},
    'enhanced': {'tl': 11, 'slots': 3, 'cost': 6000.0},
    'advanced': {'tl': 14, 'slots': 3, 'cost': 8000.0},
}

_STARSHIP_ENGINEERING_TOOLKIT_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 8, 'slots': 6, 'cost': 1000.0},
    'improved': {'tl': 10, 'slots': 5, 'cost': 2000.0},
    'enhanced': {'tl': 12, 'slots': 5, 'cost': 4000.0},
    'advanced': {'tl': 14, 'slots': 4, 'cost': 10000.0},
}

_WEAPON_MOUNT_TABLE: dict[str, dict[str, int | float]] = {
    'small': {'slots': 1, 'cost': 500.0},
    'medium': {'slots': 2, 'cost': 1000.0},
    'heavy': {'slots': 10, 'cost': 5000.0},
    'vehicle': {'slots': 15, 'cost': 10000.0},
}

_FABRICATION_CHAMBER_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 8, 'cost_per_chamber_slot': 2000.0},
    'improved': {'tl': 10, 'cost_per_chamber_slot': 10000.0},
    'enhanced': {'tl': 13, 'cost_per_chamber_slot': 50000.0},
    'advanced': {'tl': 17, 'cost_per_chamber_slot': 200000.0},
}

_MEDICAL_CHAMBER_SUB_OPTIONS: dict[str, dict[str, int | float]] = {
    'cryoberth_basic': {'tl': 10, 'slots': 8, 'cost': 20000.0},
    'cryoberth_improved': {'tl': 12, 'slots': 8, 'cost': 20000.0},
    'low_berth_basic': {'tl': 10, 'slots': 8, 'cost': 20000.0},
    'low_berth_improved': {'tl': 12, 'slots': 8, 'cost': 20000.0},
    'reanimation': {'tl': 14, 'slots': 8, 'cost': 900000.0},
    'species_specific': {'tl': 10, 'slots': 4, 'cost': 10000.0},
}


class BioscanneSensor(RobotPart):
    """refs/robot/30_no_internal_power.md — Bioscanner Sensor, TL15, 2 slots, Cr350000."""

    tl: int = 15

    @property
    def slots(self) -> int:
        return 2

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 350000.0)

    def item_description(self) -> str:
        return 'Bioscanner Sensor'


class DensitometerSensor(RobotPart):
    """refs/robot/30_no_internal_power.md — Densitometer Sensor, TL14, 3 slots, Cr20000."""

    tl: int = 14

    @property
    def slots(self) -> int:
        return 3

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 20000.0)

    def item_description(self) -> str:
        return 'Densitometer Sensor'


class NeuralActivitySensor(RobotPart):
    """refs/robot/31_neural_activity_sensor.md — Neural Activity Sensor, TL15, 5 slots, Cr35000."""

    tl: int = 15

    @property
    def slots(self) -> int:
        return 5

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'cost', 35000.0)

    def item_description(self) -> str:
        return 'Neural Activity Sensor'


class Medikit(RobotPart):
    """refs/robot/26_medikit.md — Medikit, 1 slot.

    Quality: basic (TL8, Cr1000) / improved (TL10, Cr1500) / enhanced (TL12, Cr5000) / advanced (TL14, Cr10000).
    """

    quality: str = 'basic'

    @property
    def slots(self) -> int:
        return 1

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _MEDIKIT_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def item_description(self) -> str:
        return f'Medikit ({self.quality})'


class SolarCoating(RobotPart):
    """refs/robot/13_solar_coating.md — Solar Coating.

    Zero-slot. Cost = cost_per_base_slot × base_slots.
    Not compatible with reflec or visual camouflage options.
    """

    quality: str = 'advanced'

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        tl = int(_SOLAR_COATING_TABLE[self.quality]['tl'])
        object.__setattr__(self, 'tl', tl)

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        rate = float(_SOLAR_COATING_TABLE[self.quality]['cost_per_base_slot'])
        base_slots = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', rate * base_slots)

    def item_description(self) -> str:
        return f'Solar Coating ({self.quality})'


class ScientificToolkit(RobotPart):
    """refs/robot/32_fire_extinguisher.md — Scientific Toolkit.

    Quality: basic (TL5, 4 slots, Cr2000) / improved (TL8, 3 slots, Cr4000) /
             enhanced (TL11, 3 slots, Cr6000) / advanced (TL14, 3 slots, Cr8000).
    Speciality must be specified (e.g. 'biology', 'chemistry', 'robotics').
    """

    quality: str = 'basic'
    speciality: str = ''

    @property
    def slots(self) -> int:
        return int(_SCIENTIFIC_TOOLKIT_TABLE[self.quality]['slots'])

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _SCIENTIFIC_TOOLKIT_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def item_description(self) -> str:
        if self.speciality:
            return f'Scientific Toolkit ({self.quality}, {self.speciality})'
        return f'Scientific Toolkit ({self.quality})'


class FabricationChamber(RobotPart):
    """refs/robot/28_fabrication_chamber.md — Fabrication Chamber.

    Slots = slots_count. Cost = slots_count × cost_per_chamber_slot.
    Quality: basic (TL8, Cr2000/slot) / improved (TL10, Cr10000/slot) /
             enhanced (TL13, Cr50000/slot) / advanced (TL17, Cr200000/slot).
    """

    quality: str = 'basic'
    slots_count: int = 1

    @property
    def slots(self) -> int:
        return self.slots_count

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _FABRICATION_CHAMBER_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost_per_chamber_slot']) * self.slots_count)

    def item_description(self) -> str:
        return f'Fabrication Chamber ({self.quality}, {self.slots_count} Slots)'


class MedicalChamber(RobotPart):
    """refs/robot/24_tightbeam_communicator.md — Medical Chamber.

    Base: TL8, Cr200/slot. Sub-options occupy additional slots and raise effective TL.
    low_berth: None (no berth) | 'basic' (TL10, 8 slots, Cr20000) | 'improved' (TL12, 8 slots, Cr20000)
    reanimation: TL14, 8 slots, Cr900000
    species_specific: count of species-specific add-ons (each TL10, 4 slots, Cr10000)
    """

    slots_count: int = 32
    low_berth: str | None = None
    reanimation: bool = False
    species_specific: int = 0

    @property
    def slots(self) -> int:
        total = self.slots_count
        if self.low_berth:
            total += 8
        if self.reanimation:
            total += 8
        total += self.species_specific * 4
        return total

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        eff_tl = 8
        if self.low_berth == 'basic':
            eff_tl = max(eff_tl, 10)
        elif self.low_berth == 'improved':
            eff_tl = max(eff_tl, 12)
        if self.reanimation:
            eff_tl = max(eff_tl, 14)
        if self.species_specific:
            eff_tl = max(eff_tl, 10)
        object.__setattr__(self, 'tl', eff_tl)
        base_cost = float(self.slots_count) * 200.0
        option_cost = 0.0
        if self.low_berth in ('basic', 'improved'):
            option_cost += 20000.0
        if self.reanimation:
            option_cost += 900000.0
        option_cost += self.species_specific * 10000.0
        object.__setattr__(self, 'cost', base_cost + option_cost)

    def item_description(self) -> str:
        parts: list[str] = [f'{self.slots} Slots']
        if self.low_berth == 'basic':
            parts.append('Low Berth')
        elif self.low_berth == 'improved':
            parts.append('Improved Low Berth')
        if self.reanimation:
            parts.append('Reanimation')
        if self.species_specific == 1:
            parts.append('Species-Specific Add-on')
        elif self.species_specific > 1:
            parts.append(f'Species-Specific Add-on ×{self.species_specific}')
        return 'Medical Chamber (' + ', '.join(parts) + ')'


_AUTOBAR_TABLE: dict[str, dict[str, int | float]] = {
    'basic': {'tl': 8, 'slots': 2, 'cost': 500.0},
    'improved': {'tl': 9, 'slots': 2, 'cost': 1000.0},
    'enhanced': {'tl': 10, 'slots': 2, 'cost': 2000.0},
    'advanced': {'tl': 11, 'slots': 2, 'cost': 5000.0},
}

# refs/robot/07_chassis_options.md — Robot Armour table
# (tl_min, tl_max, slot_pct, max_per_slot, cost_per_slot)
_INCREASED_ARMOUR_BANDS: list[tuple[int, int, float, int, float]] = [
    (6, 8, 0.01, 1, 250.0),
    (9, 11, 0.005, 2, 1000.0),
    (12, 14, 0.004, 3, 1500.0),
    (15, 17, 0.003, 4, 2500.0),
    (18, 999, 0.0025, 5, 5000.0),
]

# refs/robot/08_locomotion_modifications.md — Agility Enhancement cost table
# Cost = level_multiplier × Base Chassis Cost (cumulative, not per-level)
_AGILITY_COST_TABLE: dict[int, float] = {1: 1.0, 2: 2.0, 3: 4.0, 4: 8.0}


class Autobar(RobotPart):
    """refs/robot/27_autobar.md — Autobar beverage dispenser, 2 slots.

    Quality: basic (TL8, Cr500) / improved (TL9, Cr1000) / enhanced (TL10, Cr2000) / advanced (TL11, Cr5000).
    """

    quality: str = 'basic'

    @property
    def slots(self) -> int:
        return 2

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _AUTOBAR_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def item_description(self) -> str:
        return f'Autobar ({self.quality})'


class IncreasedArmour(RobotPart):
    """refs/robot/07_chassis_options.md — Increased Armour chassis modification.

    Chassis modification: adds armour points, uses slots, costs per slot.
    Slot and cost determined by robot TL and base slots at bind time.
    Does not appear in options display (chassis modification).
    """

    additional: int

    @property
    def armour_delta(self) -> int:
        return self.additional

    @property
    def slots(self) -> int:
        if self._assembly is None:
            return 0
        tl = self.assembly.tl
        base = chassis_entry(self.assembly.size).base_slots
        for tl_min, tl_max, slot_pct, max_per_slot, _cost in _INCREASED_ARMOUR_BANDS:
            if tl_min <= tl <= tl_max:
                return max(ceil(self.additional * slot_pct * base), ceil(self.additional / max_per_slot), 1)
        return 1

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        tl = assembly.tl
        base = chassis_entry(assembly.size).base_slots
        for tl_min, tl_max, slot_pct, max_per_slot, cost_per_slot in _INCREASED_ARMOUR_BANDS:
            if tl_min <= tl <= tl_max:
                slots_used = max(
                    ceil(self.additional * slot_pct * base),
                    ceil(self.additional / max_per_slot),
                    1,
                )
                object.__setattr__(self, 'cost', float(slots_used) * cost_per_slot)
                break


class AgilityEnhancement(RobotPart):
    """refs/robot/08_locomotion_modifications.md — Agility Enhancement chassis modification.

    Zero-slot. Cost = level_multiplier × BCC (cumulative). Grants Athletics (dexterity) N.
    Increases tactical speed by +N metres per Minor Action. Cannot be combined with
    TacticalSpeedReduction (RHB p.53; RIR-010). May coexist with VehicleSpeedModification — the speed
    bonus applies to tactical movement; Athletics (dexterity) and effective agility are always granted.
    """

    level: int

    @property
    def speed_bonus(self) -> int:
        return self.level

    @property
    def skill_grants(self) -> dict[str, int]:
        return {'Athletics (Dexterity)': self.level}

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        bcc = chassis_entry(assembly.size).basic_cost * assembly.locomotion.cost_multiplier
        object.__setattr__(self, 'cost', _AGILITY_COST_TABLE[self.level] * bcc)


class Efficiency(RobotPart):
    """refs/robot/07_chassis_options.md — Efficiency, TL7+.

    Zero-slot. Cost = 50% of Base Chassis Cost. Doubles endurance.
    Can be applied once, after TL endurance increase.
    """

    tl: int = 7

    @property
    def endurance_multiplier(self) -> float:
        return 2.0

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        bcc = chassis_entry(assembly.size).basic_cost * assembly.locomotion.cost_multiplier
        object.__setattr__(self, 'cost', 0.5 * bcc)

    def item_description(self) -> str:
        return 'Efficiency'


class RadiationEnvironmentProtection(RobotPart):
    """refs/robot/20_radiation_environment_protection.md — Radiation Environment Protection.

    TL7, 1 slot, Cr600 per base slot (same as VacuumEnvironmentProtection but slotted).
    """

    tl: int = 7

    @property
    def slots(self) -> int:
        return 1

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        base_slots = chassis_entry(assembly.size).base_slots
        object.__setattr__(self, 'cost', 600.0 * base_slots)

    def item_description(self) -> str:
        return 'Radiation Environment Protection'


class SecondaryLocomotion(RobotPart):
    """refs/robot/08_locomotion_modifications.md — Secondary Locomotion.

    Slots = ceil(25% × base_slots). Cost = Cr500 × slots × secondary_locomotion_multiplier.
    Grants traits from the secondary locomotion type.
    """

    locomotion: LocomotionUnion

    @property
    def slots(self) -> int:
        if self._assembly is None:
            return 0
        base = chassis_entry(self.assembly.size).base_slots
        return ceil(0.25 * base)

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        return self.locomotion.locomotion_traits

    def bind(self, assembly: RobotBase) -> None:
        super().bind(assembly)
        if assembly.tl < self.locomotion.required_tl:
            self.error(f'Secondary locomotion requires TL{self.locomotion.required_tl}, robot is TL{assembly.tl}')
        base = chassis_entry(assembly.size).base_slots
        slots_used = ceil(0.25 * base)
        object.__setattr__(self, 'cost', 500.0 * slots_used * self.locomotion.cost_multiplier)

    def item_description(self) -> str:
        return f'Secondary Locomotion ({self.locomotion.label()})'


class StarshipEngineeringToolkit(RobotPart):
    """refs/robot/32_fire_extinguisher.md — Starship Engineering Toolkit.

    Quality: basic (TL8, 6 slots, Cr1000) / improved (TL10, 5 slots, Cr2000) /
             enhanced (TL12, 5 slots, Cr4000) / advanced (TL14, 4 slots, Cr10000).
    """

    quality: str = 'basic'

    @property
    def slots(self) -> int:
        return int(_STARSHIP_ENGINEERING_TOOLKIT_TABLE[self.quality]['slots'])

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        entry = _STARSHIP_ENGINEERING_TOOLKIT_TABLE[self.quality]
        object.__setattr__(self, 'tl', int(entry['tl']))
        object.__setattr__(self, 'cost', float(entry['cost']))

    def item_description(self) -> str:
        return f'Starship Engineer Toolkit ({self.quality})'


class WeaponMount(RobotPart):
    """refs/robot/32_fire_extinguisher.md — Weapon Mount.

    Size: small (1 slot, Cr500) / medium (2 slots, Cr1000) /
          heavy (10 slots, Cr5000) / vehicle (15 slots, Cr10000).
    TL5 (no TL column in the rules table; based on design examples).
    """

    size: str = 'small'

    @property
    def slots(self) -> int:
        return int(_WEAPON_MOUNT_TABLE[self.size]['slots'])

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        object.__setattr__(self, 'tl', 5)
        object.__setattr__(self, 'cost', float(_WEAPON_MOUNT_TABLE[self.size]['cost']))

    def item_description(self) -> str:
        return f'Weapon Mount ({self.size})'


DEFAULT_SUITE_ITEM_LIMIT = 5


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
    if sum(flags) > DEFAULT_SUITE_ITEM_LIMIT:
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

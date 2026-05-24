from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import NoteList, _Note

from ..parts import CustomisableShipPart, ShipPart, SizeReduction
from .common import _GENERAL_WEAPON_MODIFICATIONS, _check_intense_focus, _damage_multiple_text

BarbetteWeapon = Literal[
    'beam_laser',
    'fusion',
    'ion_cannon',
    'missile',
    'particle',
    'plasma',
    'pulse_laser',
    'railgun',
    'torpedo',
]


class _Barbette(CustomisableShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    barbette_type: str
    weapon: ClassVar[BarbetteWeapon]
    weapon_label: ClassVar[str]
    damage_multiplier: ClassVar[int | None]
    base_cost: ClassVar[float]
    base_power: ClassVar[float]
    allowed_modifications: ClassVar[frozenset[str]] = _GENERAL_WEAPON_MODIFICATIONS | {SizeReduction.name}

    def item_description(self) -> str:
        item = f'{self.weapon_label} Barbette'
        damage_text = _damage_multiple_text(self.damage_multiplier)
        if damage_text is None:
            return item
        return f'{item} ({damage_text})'

    def build_notes(self) -> list[_Note]:
        notes = NoteList(ShipPart.build_notes(self))
        if self.customisation is not None:
            _check_intense_focus(notes, self.customisation, self.weapon)
            notes.info(self.customisation.note_text)
            for mod in self.customisation.modifications:
                notes.extend(mod.build_notes())
        return notes

    @property
    def group_key(self) -> str:
        return f'{super().group_key}|{type(self).__name__}'

    @property
    def hardpoints_required(self) -> int:
        return 1

    @property
    def crew_required_commercial(self) -> int:
        return 1

    @property
    def crew_required_military(self) -> int:
        return 2

    @property
    def tons(self) -> float:
        return 5.0 * self.tons_multiplier

    @property
    def cost(self) -> float:
        return self.base_cost * self.cost_multiplier

    @property
    def power(self) -> float:
        return self.base_power * self.power_multiplier


class BeamLaserBarbette(_Barbette):
    barbette_type: Literal['beam_laser_barbette'] = 'beam_laser_barbette'
    weapon: ClassVar[BarbetteWeapon] = 'beam_laser'
    weapon_label = 'Beam Laser'
    damage_multiplier = 3
    tl: int = 10
    base_power = 12.0
    base_cost = 3_000_000.0


class FusionBarbette(_Barbette):
    barbette_type: Literal['fusion_barbette'] = 'fusion_barbette'
    weapon: ClassVar[BarbetteWeapon] = 'fusion'
    weapon_label = 'Fusion'
    damage_multiplier = 3
    tl: int = 12
    base_power = 20.0
    base_cost = 4_000_000.0


class IonCannonBarbette(_Barbette):
    barbette_type: Literal['ion_cannon_barbette'] = 'ion_cannon_barbette'
    weapon: ClassVar[BarbetteWeapon] = 'ion_cannon'
    weapon_label = 'Ion Cannon'
    damage_multiplier = 3
    tl: int = 12
    base_power = 10.0
    base_cost = 6_000_000.0


class MissileBarbette(_Barbette):
    barbette_type: Literal['missile_barbette'] = 'missile_barbette'
    weapon: ClassVar[BarbetteWeapon] = 'missile'
    weapon_label = 'Missile'
    damage_multiplier = None
    tl: int = 7
    base_power = 0.0
    base_cost = 4_000_000.0


class ParticleBarbette(_Barbette):
    barbette_type: Literal['particle_barbette'] = 'particle_barbette'
    weapon: ClassVar[BarbetteWeapon] = 'particle'
    weapon_label = 'Particle'
    damage_multiplier = 3
    tl: int = 11
    base_power = 15.0
    base_cost = 8_000_000.0


class PlasmaBarbette(_Barbette):
    barbette_type: Literal['plasma_barbette'] = 'plasma_barbette'
    weapon: ClassVar[BarbetteWeapon] = 'plasma'
    weapon_label = 'Plasma'
    damage_multiplier = 3
    tl: int = 11
    base_power = 12.0
    base_cost = 5_000_000.0


class PulseLaserBarbette(_Barbette):
    barbette_type: Literal['pulse_laser_barbette'] = 'pulse_laser_barbette'
    weapon: ClassVar[BarbetteWeapon] = 'pulse_laser'
    weapon_label = 'Pulse Laser'
    damage_multiplier = 3
    tl: int = 9
    base_power = 12.0
    base_cost = 6_000_000.0


class RailgunBarbette(_Barbette):
    barbette_type: Literal['railgun_barbette'] = 'railgun_barbette'
    weapon: ClassVar[BarbetteWeapon] = 'railgun'
    weapon_label = 'Railgun'
    damage_multiplier = 3
    tl: int = 10
    base_power = 5.0
    base_cost = 2_000_000.0


class TorpedoBarbette(_Barbette):
    barbette_type: Literal['torpedo_barbette'] = 'torpedo_barbette'
    weapon: ClassVar[BarbetteWeapon] = 'torpedo'
    weapon_label = 'Torpedo'
    damage_multiplier = None
    tl: int = 7
    base_power = 2.0
    base_cost = 3_000_000.0


type Barbette = Annotated[
    BeamLaserBarbette
    | FusionBarbette
    | IonCannonBarbette
    | MissileBarbette
    | ParticleBarbette
    | PlasmaBarbette
    | PulseLaserBarbette
    | RailgunBarbette
    | TorpedoBarbette,
    Field(discriminator='barbette_type'),
]

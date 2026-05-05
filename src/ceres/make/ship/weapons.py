from collections.abc import Sequence
import math
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from .base import CeresModel, Note, NoteCategory
from .parts import (
    CustomisableShipPart,
    CustomisationUnion,
    EnergyEfficient,
    Modification,
    ShipPart,
    SizeReduction,
)
from .spec import ShipSpec, SpecSection
from .text import format_counted_label

LongRange = Modification(
    name='Long Range',
    advantage=2,
    info_notes=('Range increased by one band, to a maximum of Very Long',),
)

HighYield = Modification(name='High Yield', advantage=1)

VeryHighYield = Modification(name='Very High Yield', advantage=2)


def _size_reduction_steps(value: bool | int) -> int:
    return 1 if value is True else int(value)


def _damage_multiple_text(multiplier: int | None) -> str | None:
    if multiplier is None:
        return None
    return f'Damage × {multiplier} after armour'


def _mounted_weapon_label(weapon: MountWeapon) -> str:
    return weapon.build_item() or weapon.__class__.__name__


def _mounted_weapon_notes(weapons: Sequence[MountWeapon], *, empty_message: str) -> list[Note]:
    if not weapons:
        return [Note(category=NoteCategory.INFO, message=empty_message)]
    groups: dict[tuple[str, str | None], int] = {}
    order: list[tuple[str, str | None]] = []
    for weapon in weapons:
        key = (
            _mounted_weapon_label(weapon),
            None if weapon.customisation is None else weapon.customisation.note_text,
        )
        if key not in groups:
            order.append(key)
            groups[key] = 0
        groups[key] += 1

    notes: list[Note] = []
    for item, customisation in order:
        notes.append(
            Note(
                category=NoteCategory.INFO,
                message=f'Weapon: {format_counted_label(item, groups[(item, customisation)])}',
            )
        )
        if customisation is not None:
            notes.append(Note(category=NoteCategory.INFO, message=customisation))
    return notes


def _mounted_weapon_cost(weapons: Sequence[MountWeapon]) -> float:
    return sum(w.weapon_cost for w in weapons)


def _mounted_weapon_power(weapons: Sequence[MountWeapon]) -> float:
    return sum(w.weapon_power for w in weapons)


class _MountWeapon(CeresModel):
    model_config = {'frozen': True}
    weapon_type: str
    item_label: ClassVar[str]
    base_cost: ClassVar[float]
    base_power: ClassVar[float]
    high_yield_allowed: ClassVar[bool] = True
    customisation: CustomisationUnion | None = None
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            EnergyEfficient.name,
            HighYield.name,
            LongRange.name,
            VeryHighYield.name,
        }
    )

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        if self.customisation is not None:
            for mod in self.customisation.modifications:
                if mod.name not in self.allowed_modifications:
                    self.error(f'Modification not allowed for MountWeapon: {mod.name}')
            self.notes.extend(self.customisation.notes)

            if not self.high_yield_allowed:
                for mod in self.customisation.modifications:
                    if mod.name in {HighYield.name, VeryHighYield.name}:
                        self.error(f'{mod.name} is not applicable for {self.build_item()}')

    def build_item(self) -> str | None:
        return self.item_label

    def customisation_note(self) -> Note | None:
        if self.customisation is None:
            return None
        return Note(category=NoteCategory.INFO, message=self.customisation.note_text)

    @property
    def cost_modifier(self) -> float:
        return 1.0 if self.customisation is None else self.customisation.cost_multiplier

    @property
    def weapon_cost(self) -> float:
        return self.base_cost * self.cost_modifier

    @property
    def weapon_power(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return self.base_power * multiplier


class PulseLaser(_MountWeapon):
    weapon_type: Literal['pulse_laser'] = 'pulse_laser'
    item_label = 'Pulse Laser'
    base_cost = 1_000_000.0
    base_power = 4.0


class BeamLaser(_MountWeapon):
    weapon_type: Literal['beam_laser'] = 'beam_laser'
    item_label = 'Beam Laser'
    base_cost = 500_000.0
    base_power = 4.0


class MissileRack(_MountWeapon):
    weapon_type: Literal['missile_rack'] = 'missile_rack'
    item_label = 'Missile Rack'
    base_cost = 750_000.0
    base_power = 0.0
    high_yield_allowed = False


class Sandcaster(_MountWeapon):
    weapon_type: Literal['sandcaster'] = 'sandcaster'
    item_label = 'Sandcaster'
    base_cost = 250_000.0
    base_power = 0.0


type MountWeapon = Annotated[
    PulseLaser | BeamLaser | MissileRack | Sandcaster,
    Field(discriminator='weapon_type'),
]


class FixedMount(ShipPart):
    mount_cost: ClassVar[int] = 100_000
    tl: int = 9
    weapons: list[MountWeapon] = Field(default_factory=list)

    def build_item(self) -> str | None:
        if len(self.weapons) == 1:
            return self.weapons[0].build_item()
        return 'Fixed Mount'

    def build_notes(self) -> list[Note]:
        notes = super().build_notes()
        if len(self.weapons) == 1:
            cust = self.weapons[0].customisation_note()
            return [*notes, cust] if cust else notes
        return [*notes, *_mounted_weapon_notes(self.weapons, empty_message='No weapons in mount')]

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return self.mount_cost + _mounted_weapon_cost(self.weapons)

    def compute_power(self) -> float:
        power = _mounted_weapon_power(self.weapons)
        # Firmpoint reduces power by 25%; apply combined then floor
        power *= 0.75
        return float(math.floor(power))


TurretSize = Literal['single', 'double', 'triple', 'quad']


class _Turret(ShipPart):
    turret_type: str
    size: ClassVar[TurretSize]
    mount_cost: ClassVar[float]
    mount_power: ClassVar[float]
    capacity: ClassVar[int]
    weapons: list[MountWeapon] = Field(default_factory=list)

    def build_item(self) -> str | None:
        return f'{self.size.title()} Turret'

    def build_notes(self) -> list[Note]:
        return _mounted_weapon_notes(self.weapons, empty_message='No weapons in turret')

    @property
    def group_key(self) -> str:
        note_messages = tuple(note.message for note in self._display_notes_for_grouping())
        return repr((self.build_item(), note_messages))

    def _display_notes_for_grouping(self) -> list[Note]:
        return self.build_notes()

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        if len(self.weapons) > self.capacity:
            self.error(f'Turret can mount at most {self.capacity} weapon{"s" if self.capacity != 1 else ""}')

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return self.mount_cost + _mounted_weapon_cost(self.weapons)

    def compute_power(self) -> float:
        return self.mount_power + _mounted_weapon_power(self.weapons)


class SingleTurret(_Turret):
    turret_type: Literal['single_turret'] = 'single_turret'
    size: ClassVar[TurretSize] = 'single'
    tl: int = 7
    mount_cost: ClassVar[float] = 200_000.0
    mount_power: ClassVar[float] = 1.0
    capacity: ClassVar[int] = 1


class DoubleTurret(_Turret):
    turret_type: Literal['double_turret'] = 'double_turret'
    size: ClassVar[TurretSize] = 'double'
    tl: int = 8
    mount_cost: ClassVar[float] = 500_000.0
    mount_power: ClassVar[float] = 1.0
    capacity: ClassVar[int] = 2


class TripleTurret(_Turret):
    turret_type: Literal['triple_turret'] = 'triple_turret'
    size: ClassVar[TurretSize] = 'triple'
    tl: int = 9
    mount_cost: ClassVar[float] = 1_000_000.0
    mount_power: ClassVar[float] = 1.0
    capacity: ClassVar[int] = 3


class QuadTurret(_Turret):
    turret_type: Literal['quad_turret'] = 'quad_turret'
    size: ClassVar[TurretSize] = 'quad'
    tl: int = 10
    mount_cost: ClassVar[float] = 2_000_000.0
    mount_power: ClassVar[float] = 2.0
    capacity: ClassVar[int] = 4


type Turret = Annotated[
    SingleTurret | DoubleTurret | TripleTurret | QuadTurret,
    Field(discriminator='turret_type'),
]


class MissileStorage(ShipPart):
    """Magazine for missiles: 12 missiles per ton, no cost."""

    count: int

    def build_item(self) -> str | None:
        return f'Missile Storage ({self.count})'

    def compute_tons(self) -> float:
        return self.count / 12

    def compute_cost(self) -> float:
        return 0.0


class SandcasterCanisterStorage(ShipPart):
    """Magazine for sand canisters: 20 canisters per ton, no cost."""

    count: int

    def build_item(self) -> str | None:
        return f'Sandcaster Canister Storage ({self.count})'

    def compute_tons(self) -> float:
        return self.count / 20

    def compute_cost(self) -> float:
        return 0.0


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
    barbette_type: str
    weapon: ClassVar[BarbetteWeapon]
    weapon_label: ClassVar[str]
    damage_multiplier: ClassVar[int | None]
    base_cost: ClassVar[float]
    base_power: ClassVar[float]
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            SizeReduction.name,
            HighYield.name,
            VeryHighYield.name,
        }
    )

    def build_item(self) -> str | None:
        item = 'Barbette'
        damage_text = _damage_multiple_text(self.damage_multiplier)
        if damage_text is None:
            return item
        return f'{item} ({damage_text})'

    def build_notes(self) -> list[Note]:
        notes = [*ShipPart.build_notes(self)]
        notes.append(Note(category=NoteCategory.INFO, message=f'Weapon: {self.weapon_label}'))
        if self.customisation is not None:
            notes.append(Note(category=NoteCategory.INFO, message=self.customisation.note_text))
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

    def compute_tons(self) -> float:
        return 5.0 * self.tons_multiplier

    def compute_cost(self) -> float:
        return self.base_cost * self.cost_multiplier

    def compute_power(self) -> float:
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


BaySize = Literal['small', 'medium', 'large']
BayWeapon = Literal[
    'fusion_gun',
    'ion_cannon',
    'mass_driver',
    'meson_gun',
    'missile',
    'orbital_strike_mass_driver',
    'orbital_strike_missile',
    'particle_beam',
    'railgun',
    'repulsor',
    'torpedo',
]

PointDefenseKind = Literal['laser', 'gauss']
PointDefenseRating = Literal[1, 2, 3]


class _Bay(CustomisableShipPart):
    bay_type: str
    size: ClassVar[BaySize]
    weapon: ClassVar[BayWeapon]
    weapon_label: ClassVar[str]
    base_tons: ClassVar[float]
    base_cost: ClassVar[float]
    base_power: ClassVar[float]
    hardpoints: ClassVar[int]
    crew: ClassVar[int]
    damage_multiplier: ClassVar[int | None]
    salvo_text: ClassVar[str | None] = None
    magazine_summary: ClassVar[str | None] = None
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            SizeReduction.name,
            HighYield.name,
        }
    )

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        if self.customisation is None:
            return
        if self.weapon in {'missile', 'torpedo'}:
            for mod in self.customisation.modifications:
                if mod.name in {HighYield.name, VeryHighYield.name}:
                    self.error(f'{mod.name} is not applicable for {self.build_item()}')

    def build_item(self) -> str | None:
        item = f'{self.size.title()} Bay'
        if self.salvo_text is not None:
            item = f'{item} ({self.salvo_text})'
        else:
            damage_text = _damage_multiple_text(self.damage_multiplier)
            if damage_text is not None:
                item = f'{item} ({damage_text})'
        return item

    @property
    def group_key(self) -> str:
        return f'{super().group_key}|{type(self).__name__}'

    def build_notes(self) -> list[Note]:
        notes = [*ShipPart.build_notes(self)]
        notes.append(Note(category=NoteCategory.INFO, message=f'Weapon: {self.weapon_label}'))
        if self.magazine_summary is not None:
            notes.append(Note(category=NoteCategory.INFO, message=self.magazine_summary))
        if self.customisation is not None:
            notes.append(Note(category=NoteCategory.INFO, message=self.customisation.note_text))
        return notes

    @property
    def hardpoints_required(self) -> int:
        return self.hardpoints

    @property
    def crew_required_commercial(self) -> int:
        return 0

    @property
    def crew_required_military(self) -> int:
        return self.crew

    def compute_tons(self) -> float:
        return self.base_tons * self.tons_multiplier

    def compute_cost(self) -> float:
        return self.base_cost * self.cost_multiplier

    def compute_power(self) -> float:
        return self.base_power * self.power_multiplier


class _SmallBay(_Bay):
    size: ClassVar[BaySize] = 'small'
    base_tons: ClassVar[float] = 50.0
    hardpoints: ClassVar[int] = 1
    crew: ClassVar[int] = 1
    damage_multiplier: ClassVar[int | None] = 10


class _MediumBay(_Bay):
    size: ClassVar[BaySize] = 'medium'
    base_tons: ClassVar[float] = 100.0
    hardpoints: ClassVar[int] = 1
    crew: ClassVar[int] = 2
    damage_multiplier: ClassVar[int | None] = 20


class _LargeBay(_Bay):
    size: ClassVar[BaySize] = 'large'
    base_tons: ClassVar[float] = 500.0
    hardpoints: ClassVar[int] = 5
    crew: ClassVar[int] = 4
    damage_multiplier: ClassVar[int | None] = 100


class SmallFusionGunBay(_SmallBay):
    bay_type: Literal['small_fusion_gun_bay'] = 'small_fusion_gun_bay'
    weapon: ClassVar[BayWeapon] = 'fusion_gun'
    weapon_label = 'Fusion Gun'
    tl: int = 12
    base_power = 50.0
    base_cost = 8_000_000.0


class MediumFusionGunBay(_MediumBay):
    bay_type: Literal['medium_fusion_gun_bay'] = 'medium_fusion_gun_bay'
    weapon: ClassVar[BayWeapon] = 'fusion_gun'
    weapon_label = 'Fusion Gun'
    tl: int = 12
    base_power = 80.0
    base_cost = 14_000_000.0


class LargeFusionGunBay(_LargeBay):
    bay_type: Literal['large_fusion_gun_bay'] = 'large_fusion_gun_bay'
    weapon: ClassVar[BayWeapon] = 'fusion_gun'
    weapon_label = 'Fusion Gun'
    tl: int = 12
    base_power = 100.0
    base_cost = 25_000_000.0


class SmallIonCannonBay(_SmallBay):
    bay_type: Literal['small_ion_cannon_bay'] = 'small_ion_cannon_bay'
    weapon: ClassVar[BayWeapon] = 'ion_cannon'
    weapon_label = 'Ion Cannon'
    tl: int = 12
    base_power = 20.0
    base_cost = 15_000_000.0


class MediumIonCannonBay(_MediumBay):
    bay_type: Literal['medium_ion_cannon_bay'] = 'medium_ion_cannon_bay'
    weapon: ClassVar[BayWeapon] = 'ion_cannon'
    weapon_label = 'Ion Cannon'
    tl: int = 12
    base_power = 30.0
    base_cost = 25_000_000.0


class LargeIonCannonBay(_LargeBay):
    bay_type: Literal['large_ion_cannon_bay'] = 'large_ion_cannon_bay'
    weapon: ClassVar[BayWeapon] = 'ion_cannon'
    weapon_label = 'Ion Cannon'
    tl: int = 12
    base_power = 40.0
    base_cost = 40_000_000.0


class SmallMassDriverBay(_SmallBay):
    bay_type: Literal['small_mass_driver_bay'] = 'small_mass_driver_bay'
    weapon: ClassVar[BayWeapon] = 'mass_driver'
    weapon_label = 'Mass Driver'
    tl: int = 8
    base_power = 15.0
    base_cost = 40_000_000.0


class MediumMassDriverBay(_MediumBay):
    bay_type: Literal['medium_mass_driver_bay'] = 'medium_mass_driver_bay'
    weapon: ClassVar[BayWeapon] = 'mass_driver'
    weapon_label = 'Mass Driver'
    tl: int = 8
    base_power = 25.0
    base_cost = 60_000_000.0


class LargeMassDriverBay(_LargeBay):
    bay_type: Literal['large_mass_driver_bay'] = 'large_mass_driver_bay'
    weapon: ClassVar[BayWeapon] = 'mass_driver'
    weapon_label = 'Mass Driver'
    tl: int = 8
    base_power = 35.0
    base_cost = 80_000_000.0


class SmallMesonGunBay(_SmallBay):
    bay_type: Literal['small_meson_gun_bay'] = 'small_meson_gun_bay'
    weapon: ClassVar[BayWeapon] = 'meson_gun'
    weapon_label = 'Meson Gun'
    tl: int = 11
    base_power = 20.0
    base_cost = 50_000_000.0


class MediumMesonGunBay(_MediumBay):
    bay_type: Literal['medium_meson_gun_bay'] = 'medium_meson_gun_bay'
    weapon: ClassVar[BayWeapon] = 'meson_gun'
    weapon_label = 'Meson Gun'
    tl: int = 12
    base_power = 30.0
    base_cost = 60_000_000.0


class LargeMesonGunBay(_LargeBay):
    bay_type: Literal['large_meson_gun_bay'] = 'large_meson_gun_bay'
    weapon: ClassVar[BayWeapon] = 'meson_gun'
    weapon_label = 'Meson Gun'
    tl: int = 13
    base_power = 120.0
    base_cost = 250_000_000.0


class SmallMissileBay(_SmallBay):
    bay_type: Literal['small_missile_bay'] = 'small_missile_bay'
    weapon: ClassVar[BayWeapon] = 'missile'
    weapon_label = 'Missile'
    salvo_text = '12 missiles per salvo'
    magazine_summary = 'Magazine: 144 missiles (12 full salvos)'
    tl: int = 7
    base_power = 5.0
    base_cost = 12_000_000.0


class MediumMissileBay(_MediumBay):
    bay_type: Literal['medium_missile_bay'] = 'medium_missile_bay'
    weapon: ClassVar[BayWeapon] = 'missile'
    weapon_label = 'Missile'
    salvo_text = '24 missiles per salvo'
    magazine_summary = 'Magazine: 288 missiles (12 full salvos)'
    tl: int = 7
    base_power = 10.0
    base_cost = 20_000_000.0


class LargeMissileBay(_LargeBay):
    bay_type: Literal['large_missile_bay'] = 'large_missile_bay'
    weapon: ClassVar[BayWeapon] = 'missile'
    weapon_label = 'Missile'
    salvo_text = '120 missiles per salvo'
    magazine_summary = 'Magazine: 1,440 missiles (12 full salvos)'
    tl: int = 7
    base_power = 20.0
    base_cost = 25_000_000.0


class SmallOrbitalStrikeMassDriverBay(_SmallBay):
    bay_type: Literal['small_orbital_strike_mass_driver_bay'] = 'small_orbital_strike_mass_driver_bay'
    weapon: ClassVar[BayWeapon] = 'orbital_strike_mass_driver'
    weapon_label = 'Orbital Strike Mass Driver'
    tl: int = 10
    base_power = 35.0
    base_cost = 25_000_000.0


class MediumOrbitalStrikeMassDriverBay(_MediumBay):
    bay_type: Literal['medium_orbital_strike_mass_driver_bay'] = 'medium_orbital_strike_mass_driver_bay'
    weapon: ClassVar[BayWeapon] = 'orbital_strike_mass_driver'
    weapon_label = 'Orbital Strike Mass Driver'
    tl: int = 10
    base_power = 50.0
    base_cost = 35_000_000.0


class LargeOrbitalStrikeMassDriverBay(_LargeBay):
    bay_type: Literal['large_orbital_strike_mass_driver_bay'] = 'large_orbital_strike_mass_driver_bay'
    weapon: ClassVar[BayWeapon] = 'orbital_strike_mass_driver'
    weapon_label = 'Orbital Strike Mass Driver'
    tl: int = 10
    base_power = 75.0
    base_cost = 50_000_000.0


class SmallOrbitalStrikeMissileBay(_SmallBay):
    bay_type: Literal['small_orbital_strike_missile_bay'] = 'small_orbital_strike_missile_bay'
    weapon: ClassVar[BayWeapon] = 'orbital_strike_missile'
    weapon_label = 'Orbital Strike Missile'
    salvo_text = '12 missiles per salvo'
    magazine_summary = 'Magazine: 144 missiles (12 full salvos)'
    tl: int = 10
    base_power = 5.0
    base_cost = 16_000_000.0


class MediumOrbitalStrikeMissileBay(_MediumBay):
    bay_type: Literal['medium_orbital_strike_missile_bay'] = 'medium_orbital_strike_missile_bay'
    weapon: ClassVar[BayWeapon] = 'orbital_strike_missile'
    weapon_label = 'Orbital Strike Missile'
    salvo_text = '24 missiles per salvo'
    magazine_summary = 'Magazine: 288 missiles (12 full salvos)'
    tl: int = 10
    base_power = 15.0
    base_cost = 20_000_000.0


class LargeOrbitalStrikeMissileBay(_LargeBay):
    bay_type: Literal['large_orbital_strike_missile_bay'] = 'large_orbital_strike_missile_bay'
    weapon: ClassVar[BayWeapon] = 'orbital_strike_missile'
    weapon_label = 'Orbital Strike Missile'
    salvo_text = '120 missiles per salvo'
    magazine_summary = 'Magazine: 1,440 missiles (12 full salvos)'
    tl: int = 10
    base_power = 25.0
    base_cost = 24_000_000.0


class SmallParticleBeamBay(_SmallBay):
    bay_type: Literal['small_particle_beam_bay'] = 'small_particle_beam_bay'
    weapon: ClassVar[BayWeapon] = 'particle_beam'
    weapon_label = 'Particle Beam'
    tl: int = 11
    base_power = 30.0
    base_cost = 20_000_000.0


class MediumParticleBeamBay(_MediumBay):
    bay_type: Literal['medium_particle_beam_bay'] = 'medium_particle_beam_bay'
    weapon: ClassVar[BayWeapon] = 'particle_beam'
    weapon_label = 'Particle Beam'
    tl: int = 12
    base_power = 50.0
    base_cost = 40_000_000.0


class LargeParticleBeamBay(_LargeBay):
    bay_type: Literal['large_particle_beam_bay'] = 'large_particle_beam_bay'
    weapon: ClassVar[BayWeapon] = 'particle_beam'
    weapon_label = 'Particle Beam'
    tl: int = 13
    base_power = 80.0
    base_cost = 60_000_000.0


class SmallRailgunBay(_SmallBay):
    bay_type: Literal['small_railgun_bay'] = 'small_railgun_bay'
    weapon: ClassVar[BayWeapon] = 'railgun'
    weapon_label = 'Railgun'
    tl: int = 10
    base_power = 10.0
    base_cost = 30_000_000.0


class MediumRailgunBay(_MediumBay):
    bay_type: Literal['medium_railgun_bay'] = 'medium_railgun_bay'
    weapon: ClassVar[BayWeapon] = 'railgun'
    weapon_label = 'Railgun'
    tl: int = 10
    base_power = 15.0
    base_cost = 50_000_000.0


class LargeRailgunBay(_LargeBay):
    bay_type: Literal['large_railgun_bay'] = 'large_railgun_bay'
    weapon: ClassVar[BayWeapon] = 'railgun'
    weapon_label = 'Railgun'
    tl: int = 10
    base_power = 25.0
    base_cost = 70_000_000.0


class SmallRepulsorBay(_SmallBay):
    bay_type: Literal['small_repulsor_bay'] = 'small_repulsor_bay'
    weapon: ClassVar[BayWeapon] = 'repulsor'
    weapon_label = 'Repulsor'
    tl: int = 15
    base_power = 50.0
    base_cost = 30_000_000.0


class MediumRepulsorBay(_MediumBay):
    bay_type: Literal['medium_repulsor_bay'] = 'medium_repulsor_bay'
    weapon: ClassVar[BayWeapon] = 'repulsor'
    weapon_label = 'Repulsor'
    tl: int = 14
    base_power = 100.0
    base_cost = 60_000_000.0


class LargeRepulsorBay(_LargeBay):
    bay_type: Literal['large_repulsor_bay'] = 'large_repulsor_bay'
    weapon: ClassVar[BayWeapon] = 'repulsor'
    weapon_label = 'Repulsor'
    tl: int = 13
    base_power = 200.0
    base_cost = 90_000_000.0


class SmallTorpedoBay(_SmallBay):
    bay_type: Literal['small_torpedo_bay'] = 'small_torpedo_bay'
    weapon: ClassVar[BayWeapon] = 'torpedo'
    weapon_label = 'Torpedo'
    salvo_text = '3 torpedoes per salvo'
    magazine_summary = 'Magazine: 36 torpedoes (12 full salvos)'
    tl: int = 7
    base_power = 2.0
    base_cost = 3_000_000.0


class MediumTorpedoBay(_MediumBay):
    bay_type: Literal['medium_torpedo_bay'] = 'medium_torpedo_bay'
    weapon: ClassVar[BayWeapon] = 'torpedo'
    weapon_label = 'Torpedo'
    salvo_text = '6 torpedoes per salvo'
    magazine_summary = 'Magazine: 72 torpedoes (12 full salvos)'
    tl: int = 7
    base_power = 5.0
    base_cost = 6_000_000.0


class LargeTorpedoBay(_LargeBay):
    bay_type: Literal['large_torpedo_bay'] = 'large_torpedo_bay'
    weapon: ClassVar[BayWeapon] = 'torpedo'
    weapon_label = 'Torpedo'
    salvo_text = '30 torpedoes per salvo'
    magazine_summary = 'Magazine: 360 torpedoes (12 full salvos)'
    tl: int = 7
    base_power = 10.0
    base_cost = 10_000_000.0


type Bay = Annotated[
    SmallFusionGunBay
    | MediumFusionGunBay
    | LargeFusionGunBay
    | SmallIonCannonBay
    | MediumIonCannonBay
    | LargeIonCannonBay
    | SmallMassDriverBay
    | MediumMassDriverBay
    | LargeMassDriverBay
    | SmallMesonGunBay
    | MediumMesonGunBay
    | LargeMesonGunBay
    | SmallMissileBay
    | MediumMissileBay
    | LargeMissileBay
    | SmallOrbitalStrikeMassDriverBay
    | MediumOrbitalStrikeMassDriverBay
    | LargeOrbitalStrikeMassDriverBay
    | SmallOrbitalStrikeMissileBay
    | MediumOrbitalStrikeMissileBay
    | LargeOrbitalStrikeMissileBay
    | SmallParticleBeamBay
    | MediumParticleBeamBay
    | LargeParticleBeamBay
    | SmallRailgunBay
    | MediumRailgunBay
    | LargeRailgunBay
    | SmallRepulsorBay
    | MediumRepulsorBay
    | LargeRepulsorBay
    | SmallTorpedoBay
    | MediumTorpedoBay
    | LargeTorpedoBay,
    Field(discriminator='bay_type'),
]


class _PointDefenseBattery(CustomisableShipPart):
    battery_type: str
    kind: ClassVar[PointDefenseKind]
    rating: ClassVar[PointDefenseRating]
    item_label: ClassVar[str]
    base_tons: ClassVar[float]
    base_cost: ClassVar[float]
    base_power: ClassVar[float]
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            SizeReduction.name,
            EnergyEfficient.name,
        }
    )

    def build_item(self) -> str | None:
        return self.item_label

    def build_notes(self) -> list[Note]:
        notes = [*super().build_notes()]
        intercept_dice = self.rating * 2
        notes.append(Note(category=NoteCategory.INFO, message=f'Intercept +{intercept_dice}D'))
        if self.kind == 'gauss':
            notes.append(
                Note(
                    category=NoteCategory.INFO,
                    message='Requires ammunition storage to reload after 12 rounds',
                )
            )
        return notes

    @property
    def hardpoints_required(self) -> int:
        return 1

    def compute_tons(self) -> float:
        return self.base_tons * self.tons_multiplier

    def compute_cost(self) -> float:
        return self.base_cost * self.cost_multiplier

    def compute_power(self) -> float:
        return self.base_power * self.power_multiplier


class LaserPointDefenseBattery1(_PointDefenseBattery):
    battery_type: Literal['laser_point_defense_1'] = 'laser_point_defense_1'
    kind: ClassVar[PointDefenseKind] = 'laser'
    rating: ClassVar[PointDefenseRating] = 1
    item_label = 'Point Defence Laser Battery Type I'
    tl: int = 10
    base_tons = 20.0
    base_power = 10.0
    base_cost = 5_000_000.0


class LaserPointDefenseBattery2(_PointDefenseBattery):
    battery_type: Literal['laser_point_defense_2'] = 'laser_point_defense_2'
    kind: ClassVar[PointDefenseKind] = 'laser'
    rating: ClassVar[PointDefenseRating] = 2
    item_label = 'Point Defence Laser Battery Type II'
    tl: int = 12
    base_tons = 20.0
    base_power = 20.0
    base_cost = 10_000_000.0


class LaserPointDefenseBattery3(_PointDefenseBattery):
    battery_type: Literal['laser_point_defense_3'] = 'laser_point_defense_3'
    kind: ClassVar[PointDefenseKind] = 'laser'
    rating: ClassVar[PointDefenseRating] = 3
    item_label = 'Point Defence Laser Battery Type III'
    tl: int = 14
    base_tons = 20.0
    base_power = 30.0
    base_cost = 20_000_000.0


class GaussPointDefenseBattery1(_PointDefenseBattery):
    battery_type: Literal['gauss_point_defense_1'] = 'gauss_point_defense_1'
    kind: ClassVar[PointDefenseKind] = 'gauss'
    rating: ClassVar[PointDefenseRating] = 1
    item_label = 'Point Defence Gauss Battery Type I'
    tl: int = 10
    base_tons = 20.0
    base_power = 5.0
    base_cost = 3_000_000.0


class GaussPointDefenseBattery2(_PointDefenseBattery):
    battery_type: Literal['gauss_point_defense_2'] = 'gauss_point_defense_2'
    kind: ClassVar[PointDefenseKind] = 'gauss'
    rating: ClassVar[PointDefenseRating] = 2
    item_label = 'Point Defence Gauss Battery Type II'
    tl: int = 12
    base_tons = 20.0
    base_power = 15.0
    base_cost = 6_000_000.0


class GaussPointDefenseBattery3(_PointDefenseBattery):
    battery_type: Literal['gauss_point_defense_3'] = 'gauss_point_defense_3'
    kind: ClassVar[PointDefenseKind] = 'gauss'
    rating: ClassVar[PointDefenseRating] = 3
    item_label = 'Point Defence Gauss Battery Type III'
    tl: int = 14
    base_tons = 20.0
    base_power = 25.0
    base_cost = 10_000_000.0


type PointDefenseBattery = Annotated[
    LaserPointDefenseBattery1
    | LaserPointDefenseBattery2
    | LaserPointDefenseBattery3
    | GaussPointDefenseBattery1
    | GaussPointDefenseBattery2
    | GaussPointDefenseBattery3,
    Field(discriminator='battery_type'),
]


class WeaponsSection(CeresModel):
    turrets: list[Turret] = Field(default_factory=list)
    fixed_mounts: list[FixedMount] = Field(default_factory=list)
    barbettes: list[Barbette] = Field(default_factory=list)
    bays: list[Bay] = Field(default_factory=list)
    point_defense_batteries: list[PointDefenseBattery] = Field(default_factory=list)
    missile_storage: MissileStorage | None = None
    sandcaster_canister_storage: SandcasterCanisterStorage | None = None

    @staticmethod
    def is_small_craft(ship) -> bool:
        return ship.displacement < 100

    @classmethod
    def mount_capacity(cls, ship) -> int:
        if cls.is_small_craft(ship):
            if ship.displacement < 35:
                return 1
            if ship.displacement <= 70:
                return 2
            return 3
        return ship.displacement // 100

    def validate_mounting(self, ship) -> None:
        total_mounts = (
            len(self.turrets)
            + len(self.fixed_mounts)
            + sum(barbette.hardpoints_required for barbette in self.barbettes)
            + sum(bay.hardpoints_required for bay in self.bays)
            + sum(battery.hardpoints_required for battery in self.point_defense_batteries)
        )
        capacity = self.mount_capacity(ship)
        if total_mounts > capacity:
            overflow = total_mounts - capacity
            overflowing_parts = [
                *self.fixed_mounts,
                *self.turrets,
                *self.barbettes,
                *self.bays,
                *self.point_defense_batteries,
            ][-overflow:]
            mount_kind = 'firmpoints' if self.is_small_craft(ship) else 'hardpoints'
            for part in overflowing_parts:
                part.error(
                    f'Exceeds available {mount_kind}: {total_mounts} mounts installed, capacity is {capacity}',
                )

        if self.is_small_craft(ship):
            for turret in self.turrets:
                if turret.size == 'single':
                    continue
                turret.error('Small craft may only upgrade one firmpoint to a single turret')
            fixed_mount_capacity = 1
        else:
            fixed_mount_capacity = 3

        for fixed_mount in self.fixed_mounts:
            if len(fixed_mount.weapons) > fixed_mount_capacity:
                fixed_mount.error(
                    f'Fixed mount can carry at most {fixed_mount_capacity} weapon'
                    f'{"s" if fixed_mount_capacity != 1 else ""} on this ship',
                )
        if self.is_small_craft(ship):
            for bay in self.bays:
                bay.error('Bays cannot be mounted on small craft firmpoints')
            for battery in self.point_defense_batteries:
                battery.error('Point defense batteries cannot be mounted on small craft firmpoints')

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = [
            *self.turrets,
            *self.fixed_mounts,
            *self.barbettes,
            *self.bays,
            *self.point_defense_batteries,
        ]
        if self.missile_storage is not None:
            parts.append(self.missile_storage)
        if self.sandcaster_canister_storage is not None:
            parts.append(self.sandcaster_canister_storage)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for row in ship._grouped_spec_rows(SpecSection.WEAPONS, self.turrets):
            spec.add_row(row)
        for row in ship._grouped_spec_rows(SpecSection.WEAPONS, self.fixed_mounts):
            spec.add_row(row)
        for row in ship._grouped_spec_rows(SpecSection.WEAPONS, self.barbettes):
            spec.add_row(row)
        for row in ship._grouped_spec_rows(SpecSection.WEAPONS, self.bays):
            spec.add_row(row)
        for row in ship._grouped_spec_rows(SpecSection.WEAPONS, self.point_defense_batteries):
            spec.add_row(row)
        if self.missile_storage is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.WEAPONS, self.missile_storage))
        if self.sandcaster_canister_storage is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.WEAPONS, self.sandcaster_canister_storage))

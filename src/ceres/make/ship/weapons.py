from collections.abc import Sequence
import math
from typing import Annotated, Any, ClassVar, Literal

from pydantic import Field, model_validator

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


def _bay_salvo_text(weapon: BayWeapon, size: BaySize) -> str | None:
    if weapon in {'missile', 'orbital_strike_missile'}:
        per_salvo = {'small': 12, 'medium': 24, 'large': 120}[size]
        return f'{per_salvo} missiles per salvo'
    if weapon == 'torpedo':
        per_salvo = {'small': 3, 'medium': 6, 'large': 30}[size]
        return f'{per_salvo} torpedoes per salvo'
    return None


def _bay_magazine_summary(weapon: BayWeapon, size: BaySize) -> str | None:
    if weapon in {'missile', 'orbital_strike_missile'}:
        magazine = {'small': 144, 'medium': 288, 'large': 1_440}[size]
        return f'Magazine: {magazine:,} missiles (12 full salvos)'
    if weapon == 'torpedo':
        magazine = {'small': 36, 'medium': 72, 'large': 360}[size]
        return f'Magazine: {magazine:,} torpedoes (12 full salvos)'
    return None


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


MountWeaponType = Literal['pulse_laser', 'beam_laser', 'missile_rack', 'sandcaster']


class MountWeapon(CeresModel):
    model_config = {'frozen': True}
    _specs: ClassVar[dict[MountWeaponType, dict[str, float | str]]] = dict(
        pulse_laser=dict(item='Pulse Laser', cost=1_000_000, power=4),
        beam_laser=dict(item='Beam Laser', cost=500_000, power=4),
        missile_rack=dict(item='Missile Rack', cost=750_000, power=0),
        sandcaster=dict(item='Sandcaster', cost=250_000, power=0),
    )
    weapon: MountWeaponType
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

            if self.weapon in {'missile_rack'}:
                for mod in self.customisation.modifications:
                    if mod.name in {HighYield.name, VeryHighYield.name}:
                        self.error(f'{mod.name} is not applicable for {self.build_item()}')

    @property
    def base_cost(self) -> float:
        return float(self._specs[self.weapon]['cost'])

    @property
    def base_power(self) -> float:
        return float(self._specs[self.weapon]['power'])

    def build_item(self) -> str | None:
        return str(self._specs[self.weapon]['item'])

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
        notes.append(Note(category=NoteCategory.INFO, message=f'Weapon: {self._weapon_specs_label}'))
        if self.customisation is not None:
            notes.append(Note(category=NoteCategory.INFO, message=self.customisation.note_text))
        return notes

    @property
    def group_key(self) -> str:
        return f'{super().group_key}|weapon={self.weapon}'

    @property
    def _weapon_specs_label(self) -> str:
        return self.weapon_label

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
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return 5.0 * multiplier

    def compute_cost(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return self.base_cost * multiplier

    def compute_power(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return self.base_power * multiplier


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


class Bay(CustomisableShipPart):
    _size_specs: ClassVar[dict[BaySize, dict[str, int]]] = dict(
        small=dict(tons=50, hardpoints=1, crew=1),
        medium=dict(tons=100, hardpoints=1, crew=2),
        large=dict(tons=500, hardpoints=5, crew=4),
    )
    _weapon_specs: ClassVar[dict[BayWeapon, dict[BaySize, dict[str, float | int | str]]]] = dict(
        fusion_gun=dict(
            small=dict(item='Small Fusion Gun Bay', tl=12, power=50, cost=8_000_000),
            medium=dict(item='Medium Fusion Gun Bay', tl=12, power=80, cost=14_000_000),
            large=dict(item='Large Fusion Gun Bay', tl=12, power=100, cost=25_000_000),
        ),
        ion_cannon=dict(
            small=dict(item='Small Ion Cannon Bay', tl=12, power=20, cost=15_000_000),
            medium=dict(item='Medium Ion Cannon Bay', tl=12, power=30, cost=25_000_000),
            large=dict(item='Large Ion Cannon Bay', tl=12, power=40, cost=40_000_000),
        ),
        mass_driver=dict(
            small=dict(item='Small Mass Driver Bay', tl=8, power=15, cost=40_000_000),
            medium=dict(item='Medium Mass Driver Bay', tl=8, power=25, cost=60_000_000),
            large=dict(item='Large Mass Driver Bay', tl=8, power=35, cost=80_000_000),
        ),
        meson_gun=dict(
            small=dict(item='Small Meson Gun Bay', tl=11, power=20, cost=50_000_000),
            medium=dict(item='Medium Meson Gun Bay', tl=12, power=30, cost=60_000_000),
            large=dict(item='Large Meson Gun Bay', tl=13, power=120, cost=250_000_000),
        ),
        missile=dict(
            small=dict(item='Small Missile Bay', tl=7, power=5, cost=12_000_000),
            medium=dict(item='Medium Missile Bay', tl=7, power=10, cost=20_000_000),
            large=dict(item='Large Missile Bay', tl=7, power=20, cost=25_000_000),
        ),
        orbital_strike_mass_driver=dict(
            small=dict(item='Small Orbital Strike Mass Driver Bay', tl=10, power=35, cost=25_000_000),
            medium=dict(item='Medium Orbital Strike Mass Driver Bay', tl=10, power=50, cost=35_000_000),
            large=dict(item='Large Orbital Strike Mass Driver Bay', tl=10, power=75, cost=50_000_000),
        ),
        orbital_strike_missile=dict(
            small=dict(item='Small Orbital Strike Missile Bay', tl=10, power=5, cost=16_000_000),
            medium=dict(item='Medium Orbital Strike Missile Bay', tl=10, power=15, cost=20_000_000),
            large=dict(item='Large Orbital Strike Missile Bay', tl=10, power=25, cost=24_000_000),
        ),
        particle_beam=dict(
            small=dict(item='Small Particle Beam Bay', tl=11, power=30, cost=20_000_000),
            medium=dict(item='Medium Particle Beam Bay', tl=12, power=50, cost=40_000_000),
            large=dict(item='Large Particle Beam Bay', tl=13, power=80, cost=60_000_000),
        ),
        railgun=dict(
            small=dict(item='Small Railgun Bay', tl=10, power=10, cost=30_000_000),
            medium=dict(item='Medium Railgun Bay', tl=10, power=15, cost=50_000_000),
            large=dict(item='Large Railgun Bay', tl=10, power=25, cost=70_000_000),
        ),
        repulsor=dict(
            small=dict(item='Small Repulsor Bay', tl=15, power=50, cost=30_000_000),
            medium=dict(item='Medium Repulsor Bay', tl=14, power=100, cost=60_000_000),
            large=dict(item='Large Repulsor Bay', tl=13, power=200, cost=90_000_000),
        ),
        torpedo=dict(
            small=dict(item='Small Torpedo Bay', tl=7, power=2, cost=3_000_000),
            medium=dict(item='Medium Torpedo Bay', tl=7, power=5, cost=6_000_000),
            large=dict(item='Large Torpedo Bay', tl=7, power=10, cost=10_000_000),
        ),
    )
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            SizeReduction.name,
            HighYield.name,
        }
    )
    _damage_multiplier: ClassVar[dict[BaySize, int]] = {
        'small': 10,
        'medium': 20,
        'large': 100,
    }
    _weapon_labels: ClassVar[dict[BayWeapon, str]] = {
        'fusion_gun': 'Fusion Gun',
        'ion_cannon': 'Ion Cannon',
        'mass_driver': 'Mass Driver',
        'meson_gun': 'Meson Gun',
        'missile': 'Missile',
        'orbital_strike_mass_driver': 'Orbital Strike Mass Driver',
        'orbital_strike_missile': 'Orbital Strike Missile',
        'particle_beam': 'Particle Beam',
        'railgun': 'Railgun',
        'repulsor': 'Repulsor',
        'torpedo': 'Torpedo',
    }
    size: BaySize
    weapon: BayWeapon

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
        salvo_text = _bay_salvo_text(self.weapon, self.size)
        if salvo_text is not None:
            item = f'{item} ({salvo_text})'
        elif self.weapon not in {'missile', 'torpedo', 'orbital_strike_missile'}:
            damage_text = _damage_multiple_text(self._damage_multiplier[self.size])
            if damage_text is not None:
                item = f'{item} ({damage_text})'
        return item

    @property
    def group_key(self) -> str:
        return f'{super().group_key}|weapon={self.weapon}'

    @model_validator(mode='before')
    @classmethod
    def _fill_tl(cls, data: Any) -> Any:
        if isinstance(data, dict) and 'tl' not in data:
            weapon = data.get('weapon')
            size = data.get('size')
            if weapon is not None and size is not None:
                weapon_specs = cls._weapon_specs.get(weapon)
                if weapon_specs is not None:
                    size_specs = weapon_specs.get(size)
                    if size_specs is not None:
                        data = {**data, 'tl': int(size_specs['tl'])}
        return data

    def build_notes(self) -> list[Note]:
        notes = [*ShipPart.build_notes(self)]
        notes.append(Note(category=NoteCategory.INFO, message=f'Weapon: {self._weapon_labels[self.weapon]}'))
        magazine_summary = _bay_magazine_summary(self.weapon, self.size)
        if magazine_summary is not None:
            notes.append(Note(category=NoteCategory.INFO, message=magazine_summary))
        if self.customisation is not None:
            notes.append(Note(category=NoteCategory.INFO, message=self.customisation.note_text))
        return notes

    @property
    def hardpoints_required(self) -> int:
        return self._size_specs[self.size]['hardpoints']

    @property
    def crew_required_commercial(self) -> int:
        return 0

    @property
    def crew_required_military(self) -> int:
        return self._size_specs[self.size]['crew']

    def compute_tons(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return float(self._size_specs[self.size]['tons']) * multiplier

    def compute_cost(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return float(self._weapon_specs[self.weapon][self.size]['cost']) * multiplier

    def compute_power(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return float(self._weapon_specs[self.weapon][self.size]['power']) * multiplier


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
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return self.base_tons * multiplier

    def compute_cost(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return self.base_cost * multiplier

    def compute_power(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return self.base_power * multiplier


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

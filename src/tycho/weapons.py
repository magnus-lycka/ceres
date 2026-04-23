from collections.abc import Sequence
import math
from typing import ClassVar, Literal

from pydantic import AliasChoices, Field

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


MountWeaponType = Literal['pulse_laser', 'beam_laser', 'missile_rack']


class MountWeapon(CeresModel):
    model_config = {'frozen': True}
    _specs: ClassVar[dict[MountWeaponType, dict[str, float | str]]] = dict(
        pulse_laser=dict(item='Pulse Laser', cost=1_000_000, power=4),
        beam_laser=dict(item='Beam Laser', cost=500_000, power=4),
        missile_rack=dict(item='Missile Rack', cost=750_000, power=0),
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
    minimum_tl = 9
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


TurretSize = Literal['single', 'double', 'triple']


class Turret(ShipPart):
    _specs: ClassVar[dict[TurretSize, dict[str, float | int | str]]] = dict(
        single=dict(item='Single Turret', minimum_tl=7, mount_cost=200_000, capacity=1),
        double=dict(item='Double Turret', minimum_tl=8, mount_cost=500_000, capacity=2),
        triple=dict(item='Triple Turret', minimum_tl=9, mount_cost=1_000_000, capacity=3),
    )
    size: TurretSize
    weapons: list[MountWeapon] = Field(default_factory=list)

    def build_item(self) -> str | None:
        return str(self._specs[self.size]['item'])

    def build_notes(self) -> list[Note]:
        return _mounted_weapon_notes(self.weapons, empty_message='No weapons in turret')

    @property
    def group_key(self) -> str:
        note_messages = tuple(note.message for note in self._display_notes_for_grouping())
        return repr((self.build_item(), note_messages))

    def _display_notes_for_grouping(self) -> list[Note]:
        return self.build_notes()

    @property
    def minimum_tl(self) -> int:  # type: ignore[override]
        return int(self._specs[self.size]['minimum_tl'])

    @property
    def capacity(self) -> int:
        return int(self._specs[self.size]['capacity'])

    @property
    def mount_cost(self) -> float:
        return float(self._specs[self.size]['mount_cost'])

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        if len(self.weapons) > self.capacity:
            self.error(f'Turret can mount at most {self.capacity} weapon{"s" if self.capacity != 1 else ""}')

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return self.mount_cost + _mounted_weapon_cost(self.weapons)

    def compute_power(self) -> float:
        return 1.0 + _mounted_weapon_power(self.weapons)


class MissileStorage(ShipPart):
    """Magazine for missiles: 12 missiles per ton, no cost."""

    count: int

    def build_item(self) -> str | None:
        return f'Missile Storage ({self.count})'

    def compute_tons(self) -> float:
        return self.count / 12

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


class Barbette(CustomisableShipPart):
    _specs: ClassVar[dict[BarbetteWeapon, dict[str, float | int | str]]] = dict(
        beam_laser=dict(item='Beam Laser Barbette', minimum_tl=10, power=12, cost=3_000_000),
        fusion=dict(item='Fusion Barbette', minimum_tl=12, power=20, cost=4_000_000),
        ion_cannon=dict(item='Ion Cannon', minimum_tl=12, power=10, cost=6_000_000),
        missile=dict(item='Missile Barbette', minimum_tl=7, power=0, cost=4_000_000),
        particle=dict(item='Particle Barbette', minimum_tl=11, power=15, cost=8_000_000),
        plasma=dict(item='Plasma Barbette', minimum_tl=11, power=12, cost=5_000_000),
        pulse_laser=dict(item='Pulse Laser Barbette', minimum_tl=9, power=12, cost=6_000_000),
        railgun=dict(item='Railgun Barbette', minimum_tl=10, power=5, cost=2_000_000),
        torpedo=dict(item='Torpedo', minimum_tl=7, power=2, cost=3_000_000),
    )
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            SizeReduction.name,
            HighYield.name,
            VeryHighYield.name,
        }
    )
    _damage_multiplier: ClassVar[dict[BarbetteWeapon, int | None]] = {
        'beam_laser': 3,
        'fusion': 3,
        'ion_cannon': 3,
        'missile': None,
        'particle': 3,
        'plasma': 3,
        'pulse_laser': 3,
        'railgun': 3,
        'torpedo': None,
    }
    weapon: BarbetteWeapon

    def build_item(self) -> str | None:
        item = 'Barbette'
        damage_text = _damage_multiple_text(self._damage_multiplier[self.weapon])
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
        item = str(self._specs[self.weapon]['item'])
        return item.removesuffix(' Barbette')

    @property
    def minimum_tl(self) -> int:  # type: ignore[override]
        return int(self._specs[self.weapon]['minimum_tl'])

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
        return float(self._specs[self.weapon]['cost']) * multiplier

    def compute_power(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return float(self._specs[self.weapon]['power']) * multiplier


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
            small=dict(item='Small Fusion Gun Bay', minimum_tl=12, power=50, cost=8_000_000),
            medium=dict(item='Medium Fusion Gun Bay', minimum_tl=12, power=80, cost=14_000_000),
            large=dict(item='Large Fusion Gun Bay', minimum_tl=12, power=100, cost=25_000_000),
        ),
        ion_cannon=dict(
            small=dict(item='Small Ion Cannon Bay', minimum_tl=12, power=20, cost=15_000_000),
            medium=dict(item='Medium Ion Cannon Bay', minimum_tl=12, power=30, cost=25_000_000),
            large=dict(item='Large Ion Cannon Bay', minimum_tl=12, power=40, cost=40_000_000),
        ),
        mass_driver=dict(
            small=dict(item='Small Mass Driver Bay', minimum_tl=8, power=15, cost=40_000_000),
            medium=dict(item='Medium Mass Driver Bay', minimum_tl=8, power=25, cost=60_000_000),
            large=dict(item='Large Mass Driver Bay', minimum_tl=8, power=35, cost=80_000_000),
        ),
        meson_gun=dict(
            small=dict(item='Small Meson Gun Bay', minimum_tl=11, power=20, cost=50_000_000),
            medium=dict(item='Medium Meson Gun Bay', minimum_tl=12, power=30, cost=60_000_000),
            large=dict(item='Large Meson Gun Bay', minimum_tl=13, power=120, cost=250_000_000),
        ),
        missile=dict(
            small=dict(item='Small Missile Bay', minimum_tl=7, power=5, cost=12_000_000),
            medium=dict(item='Medium Missile Bay', minimum_tl=7, power=10, cost=20_000_000),
            large=dict(item='Large Missile Bay', minimum_tl=7, power=20, cost=25_000_000),
        ),
        orbital_strike_mass_driver=dict(
            small=dict(item='Small Orbital Strike Mass Driver Bay', minimum_tl=10, power=35, cost=25_000_000),
            medium=dict(item='Medium Orbital Strike Mass Driver Bay', minimum_tl=10, power=50, cost=35_000_000),
            large=dict(item='Large Orbital Strike Mass Driver Bay', minimum_tl=10, power=75, cost=50_000_000),
        ),
        orbital_strike_missile=dict(
            small=dict(item='Small Orbital Strike Missile Bay', minimum_tl=10, power=5, cost=16_000_000),
            medium=dict(item='Medium Orbital Strike Missile Bay', minimum_tl=10, power=15, cost=20_000_000),
            large=dict(item='Large Orbital Strike Missile Bay', minimum_tl=10, power=25, cost=24_000_000),
        ),
        particle_beam=dict(
            small=dict(item='Small Particle Beam Bay', minimum_tl=11, power=30, cost=20_000_000),
            medium=dict(item='Medium Particle Beam Bay', minimum_tl=12, power=50, cost=40_000_000),
            large=dict(item='Large Particle Beam Bay', minimum_tl=13, power=80, cost=60_000_000),
        ),
        railgun=dict(
            small=dict(item='Small Railgun Bay', minimum_tl=10, power=10, cost=30_000_000),
            medium=dict(item='Medium Railgun Bay', minimum_tl=10, power=15, cost=50_000_000),
            large=dict(item='Large Railgun Bay', minimum_tl=10, power=25, cost=70_000_000),
        ),
        repulsor=dict(
            small=dict(item='Small Repulsor Bay', minimum_tl=15, power=50, cost=30_000_000),
            medium=dict(item='Medium Repulsor Bay', minimum_tl=14, power=100, cost=60_000_000),
            large=dict(item='Large Repulsor Bay', minimum_tl=13, power=200, cost=90_000_000),
        ),
        torpedo=dict(
            small=dict(item='Small Torpedo Bay', minimum_tl=7, power=2, cost=3_000_000),
            medium=dict(item='Medium Torpedo Bay', minimum_tl=7, power=5, cost=6_000_000),
            large=dict(item='Large Torpedo Bay', minimum_tl=7, power=10, cost=10_000_000),
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
    def minimum_tl(self) -> int:  # type: ignore[override]
        return int(self._weapon_specs[self.weapon][self.size]['minimum_tl'])

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


class PointDefenseBattery(CustomisableShipPart):
    _specs: ClassVar[dict[PointDefenseKind, dict[PointDefenseRating, dict[str, float | int | str]]]] = dict(
        laser={
            1: dict(item='Point Defence Laser Battery Type I', minimum_tl=10, power=10, tons=20, cost=5_000_000),
            2: dict(item='Point Defence Laser Battery Type II', minimum_tl=12, power=20, tons=20, cost=10_000_000),
            3: dict(item='Point Defence Laser Battery Type III', minimum_tl=14, power=30, tons=20, cost=20_000_000),
        },
        gauss={
            1: dict(item='Point Defence Gauss Battery Type I', minimum_tl=10, power=5, tons=20, cost=3_000_000),
            2: dict(item='Point Defence Gauss Battery Type II', minimum_tl=12, power=15, tons=20, cost=6_000_000),
            3: dict(item='Point Defence Gauss Battery Type III', minimum_tl=14, power=25, tons=20, cost=10_000_000),
        },
    )
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            SizeReduction.name,
            EnergyEfficient.name,
        }
    )
    kind: PointDefenseKind
    rating: PointDefenseRating

    def build_item(self) -> str | None:
        return str(self._specs[self.kind][self.rating]['item'])

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
    def minimum_tl(self) -> int:  # type: ignore[override]
        return int(self._specs[self.kind][self.rating]['minimum_tl'])

    @property
    def hardpoints_required(self) -> int:
        return 1

    def compute_tons(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.tons_multiplier
        return float(self._specs[self.kind][self.rating]['tons']) * multiplier

    def compute_cost(self) -> float:
        multiplier = 1.0 if self.customisation is None else self.customisation.cost_multiplier
        return float(self._specs[self.kind][self.rating]['cost']) * multiplier

    def compute_power(self) -> float:
        power = float(self._specs[self.kind][self.rating]['power'])
        multiplier = 1.0 if self.customisation is None else self.customisation.power_multiplier
        return power * multiplier


class WeaponsSection(CeresModel):
    turrets: list[Turret] = Field(default_factory=list)
    fixed_mounts: list[FixedMount] = Field(
        default_factory=list,
        validation_alias=AliasChoices('fixed_mounts', 'fixed_firmpoints'),
    )
    barbettes: list[Barbette] = Field(default_factory=list)
    bays: list[Bay] = Field(default_factory=list)
    point_defense_batteries: list[PointDefenseBattery] = Field(default_factory=list)
    missile_storage: MissileStorage | None = None

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

import math
from typing import Annotated, ClassVar, Literal

from pydantic import AliasChoices, Field

from .base import CeresModel, Note, NoteCategory
from .parts import ShipPart
from .spec import ShipSpec, SpecSection


class PulseLaser(CeresModel):
    """Pulse laser weapon (TL9, 2D damage, Long range)."""

    model_config = {'frozen': True}
    weapon_type: Literal['pulse_laser'] = 'pulse_laser'
    base_cost: ClassVar[int] = 1_000_000
    base_power: ClassVar[int] = 4

    very_high_yield: bool = False  # 2 advantages
    energy_efficient: bool = False  # 1 advantage

    def build_item(self) -> str | None:
        parts = ['Pulse Laser']
        if self.very_high_yield:
            parts.append('Very High Yield')
        if self.energy_efficient:
            parts.append('Energy Efficient')
        return ', '.join(parts)

    @property
    def cost_modifier(self) -> float:
        advantages = 0
        if self.very_high_yield:
            advantages += 2
        if self.energy_efficient:
            advantages += 1
        # Prototype/Advanced table
        if advantages >= 3:
            return 1.50  # High Technology
        if advantages == 2:
            return 1.25  # Very Advanced
        if advantages == 1:
            return 1.10  # Advanced
        return 1.0

    @property
    def weapon_cost(self) -> float:
        return self.base_cost * self.cost_modifier

    @property
    def weapon_power(self) -> float:
        if self.energy_efficient:
            return self.base_power * 0.75
        return float(self.base_power)


class FixedMount(ShipPart):
    mount_cost: ClassVar[int] = 100_000
    minimum_tl = 9
    weapon: TurretWeapon | None = None
    weapons: list[TurretWeapon] = Field(default_factory=list)

    def build_item(self) -> str | None:
        if len(self.weapons) == 1:
            return self.weapons[0].build_item()
        return 'Fixed Mount'

    def build_notes(self) -> list[Note]:
        if not self.weapons:
            return [Note(category=NoteCategory.INFO, message='No weapons in mount')]
        if len(self.weapons) == 1:
            return []
        return [Note(category=NoteCategory.INFO, message=w.build_item() or w.__class__.__name__) for w in self.weapons]

    def model_post_init(self, __context) -> None:
        if self.weapon is not None and not self.weapons:
            object.__setattr__(self, 'weapons', [self.weapon])
        super().model_post_init(__context)

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return self.mount_cost + sum(w.weapon_cost for w in self.weapons)

    def compute_power(self) -> float:
        power = sum(w.weapon_power for w in self.weapons)
        # Firmpoint reduces power by 25%; apply combined then floor
        power *= 0.75
        return float(math.floor(power))


class TurretBeamLaser(CeresModel):
    weapon_type: Literal['beam_laser'] = 'beam_laser'
    model_config = {'frozen': True}
    weapon_cost: ClassVar[int] = 500_000
    weapon_power: ClassVar[int] = 4

    def build_item(self) -> str | None:
        return 'Beam Laser'


class TurretMissileRack(CeresModel):
    weapon_type: Literal['missile_rack'] = 'missile_rack'
    model_config = {'frozen': True}
    weapon_cost: ClassVar[int] = 750_000
    weapon_power: ClassVar[int] = 0

    def build_item(self) -> str | None:
        return 'Missile Rack'


TurretWeapon = Annotated[PulseLaser | TurretBeamLaser | TurretMissileRack, Field(discriminator='weapon_type')]


class TurretMount(ShipPart):
    weapons: list[TurretWeapon] = Field(default_factory=list)
    mount_cost: ClassVar[float]
    capacity: ClassVar[int]

    def build_notes(self) -> list[Note]:
        if not self.weapons:
            return [Note(category=NoteCategory.INFO, message='No weapons in turret')]
        return [Note(category=NoteCategory.INFO, message=w.build_item() or w.__class__.__name__) for w in self.weapons]

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        if len(self.weapons) > self.capacity:
            self.error(f'Turret can mount at most {self.capacity} weapon{"s" if self.capacity != 1 else ""}')

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return self.mount_cost + sum(w.weapon_cost for w in self.weapons)

    def compute_power(self) -> float:
        return 1.0 + sum(w.weapon_power for w in self.weapons)


class SingleTurret(TurretMount):
    mount_type: Literal['single'] = 'single'
    minimum_tl = 7
    mount_cost = 200_000.0
    capacity = 1

    def build_item(self) -> str | None:
        return 'Single Turret'


class DoubleTurret(TurretMount):
    mount_type: Literal['double'] = 'double'
    minimum_tl = 8
    mount_cost = 500_000.0
    capacity = 2

    def build_item(self) -> str | None:
        return 'Double Turret'


class TripleTurret(TurretMount):
    mount_type: Literal['triple'] = 'triple'
    minimum_tl = 9
    mount_cost = 1_000_000.0
    capacity = 3

    def build_item(self) -> str | None:
        return 'Triple Turret'


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

BARBETTE_SPECS: dict[BarbetteWeapon, dict[str, float | int | str]] = {
    'beam_laser': {'item': 'Beam Laser Barbette', 'minimum_tl': 10, 'power': 12, 'cost': 3_000_000},
    'fusion': {'item': 'Fusion Barbette', 'minimum_tl': 12, 'power': 20, 'cost': 4_000_000},
    'ion_cannon': {'item': 'Ion Cannon', 'minimum_tl': 12, 'power': 10, 'cost': 6_000_000},
    'missile': {'item': 'Missile Barbette', 'minimum_tl': 7, 'power': 0, 'cost': 4_000_000},
    'particle': {'item': 'Particle Barbette', 'minimum_tl': 11, 'power': 15, 'cost': 8_000_000},
    'plasma': {'item': 'Plasma Barbette', 'minimum_tl': 11, 'power': 12, 'cost': 5_000_000},
    'pulse_laser': {'item': 'Pulse Laser Barbette', 'minimum_tl': 9, 'power': 12, 'cost': 6_000_000},
    'railgun': {'item': 'Railgun Barbette', 'minimum_tl': 10, 'power': 5, 'cost': 2_000_000},
    'torpedo': {'item': 'Torpedo', 'minimum_tl': 7, 'power': 2, 'cost': 3_000_000},
}


class Barbette(ShipPart):
    weapon: BarbetteWeapon

    def build_item(self) -> str | None:
        return str(BARBETTE_SPECS[self.weapon]['item'])

    @property
    def minimum_tl(self) -> int:  # type: ignore[override]
        return int(BARBETTE_SPECS[self.weapon]['minimum_tl'])

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
        return 5.0

    def compute_cost(self) -> float:
        return float(BARBETTE_SPECS[self.weapon]['cost'])

    def compute_power(self) -> float:
        return float(BARBETTE_SPECS[self.weapon]['power'])


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

BAY_SIZE_SPECS: dict[BaySize, dict[str, int]] = {
    'small': {'tons': 50, 'hardpoints': 1, 'crew': 1},
    'medium': {'tons': 100, 'hardpoints': 1, 'crew': 2},
    'large': {'tons': 500, 'hardpoints': 5, 'crew': 4},
}

BAY_WEAPON_SPECS: dict[BayWeapon, dict[BaySize, dict[str, float | int | str]]] = {
    'fusion_gun': {
        'small': {'item': 'Small Fusion Gun Bay', 'minimum_tl': 12, 'power': 50, 'cost': 8_000_000},
        'medium': {'item': 'Medium Fusion Gun Bay', 'minimum_tl': 12, 'power': 80, 'cost': 14_000_000},
        'large': {'item': 'Large Fusion Gun Bay', 'minimum_tl': 12, 'power': 100, 'cost': 25_000_000},
    },
    'ion_cannon': {
        'small': {'item': 'Small Ion Cannon Bay', 'minimum_tl': 12, 'power': 20, 'cost': 15_000_000},
        'medium': {'item': 'Medium Ion Cannon Bay', 'minimum_tl': 12, 'power': 30, 'cost': 25_000_000},
        'large': {'item': 'Large Ion Cannon Bay', 'minimum_tl': 12, 'power': 40, 'cost': 40_000_000},
    },
    'mass_driver': {
        'small': {'item': 'Small Mass Driver Bay', 'minimum_tl': 8, 'power': 15, 'cost': 40_000_000},
        'medium': {'item': 'Medium Mass Driver Bay', 'minimum_tl': 8, 'power': 25, 'cost': 60_000_000},
        'large': {'item': 'Large Mass Driver Bay', 'minimum_tl': 8, 'power': 35, 'cost': 80_000_000},
    },
    'meson_gun': {
        'small': {'item': 'Small Meson Gun Bay', 'minimum_tl': 11, 'power': 20, 'cost': 50_000_000},
        'medium': {'item': 'Medium Meson Gun Bay', 'minimum_tl': 12, 'power': 30, 'cost': 60_000_000},
        'large': {'item': 'Large Meson Gun Bay', 'minimum_tl': 13, 'power': 120, 'cost': 250_000_000},
    },
    'missile': {
        'small': {'item': 'Small Missile Bay', 'minimum_tl': 7, 'power': 5, 'cost': 12_000_000},
        'medium': {'item': 'Medium Missile Bay', 'minimum_tl': 7, 'power': 10, 'cost': 20_000_000},
        'large': {'item': 'Large Missile Bay', 'minimum_tl': 7, 'power': 20, 'cost': 25_000_000},
    },
    'orbital_strike_mass_driver': {
        'small': {'item': 'Small Orbital Strike Mass Driver Bay', 'minimum_tl': 10, 'power': 35, 'cost': 25_000_000},
        'medium': {'item': 'Medium Orbital Strike Mass Driver Bay', 'minimum_tl': 10, 'power': 50, 'cost': 35_000_000},
        'large': {'item': 'Large Orbital Strike Mass Driver Bay', 'minimum_tl': 10, 'power': 75, 'cost': 50_000_000},
    },
    'orbital_strike_missile': {
        'small': {'item': 'Small Orbital Strike Missile Bay', 'minimum_tl': 10, 'power': 5, 'cost': 16_000_000},
        'medium': {'item': 'Medium Orbital Strike Missile Bay', 'minimum_tl': 10, 'power': 15, 'cost': 20_000_000},
        'large': {'item': 'Large Orbital Strike Missile Bay', 'minimum_tl': 10, 'power': 25, 'cost': 24_000_000},
    },
    'particle_beam': {
        'small': {'item': 'Small Particle Beam Bay', 'minimum_tl': 11, 'power': 30, 'cost': 20_000_000},
        'medium': {'item': 'Medium Particle Beam Bay', 'minimum_tl': 12, 'power': 50, 'cost': 40_000_000},
        'large': {'item': 'Large Particle Beam Bay', 'minimum_tl': 13, 'power': 80, 'cost': 60_000_000},
    },
    'railgun': {
        'small': {'item': 'Small Railgun Bay', 'minimum_tl': 10, 'power': 10, 'cost': 30_000_000},
        'medium': {'item': 'Medium Railgun Bay', 'minimum_tl': 10, 'power': 15, 'cost': 50_000_000},
        'large': {'item': 'Large Railgun Bay', 'minimum_tl': 10, 'power': 25, 'cost': 70_000_000},
    },
    'repulsor': {
        'small': {'item': 'Small Repulsor Bay', 'minimum_tl': 15, 'power': 50, 'cost': 30_000_000},
        'medium': {'item': 'Medium Repulsor Bay', 'minimum_tl': 14, 'power': 100, 'cost': 60_000_000},
        'large': {'item': 'Large Repulsor Bay', 'minimum_tl': 13, 'power': 200, 'cost': 90_000_000},
    },
    'torpedo': {
        'small': {'item': 'Small Torpedo Bay', 'minimum_tl': 7, 'power': 2, 'cost': 3_000_000},
        'medium': {'item': 'Medium Torpedo Bay', 'minimum_tl': 7, 'power': 5, 'cost': 6_000_000},
        'large': {'item': 'Large Torpedo Bay', 'minimum_tl': 7, 'power': 10, 'cost': 10_000_000},
    },
}


class Bay(ShipPart):
    size: BaySize
    weapon: BayWeapon

    def build_item(self) -> str | None:
        return str(BAY_WEAPON_SPECS[self.weapon][self.size]['item'])

    @property
    def minimum_tl(self) -> int:  # type: ignore[override]
        return int(BAY_WEAPON_SPECS[self.weapon][self.size]['minimum_tl'])

    @property
    def hardpoints_required(self) -> int:
        return BAY_SIZE_SPECS[self.size]['hardpoints']

    @property
    def crew_required_commercial(self) -> int:
        return 0

    @property
    def crew_required_military(self) -> int:
        return BAY_SIZE_SPECS[self.size]['crew']

    def compute_tons(self) -> float:
        return float(BAY_SIZE_SPECS[self.size]['tons'])

    def compute_cost(self) -> float:
        return float(BAY_WEAPON_SPECS[self.weapon][self.size]['cost'])

    def compute_power(self) -> float:
        return float(BAY_WEAPON_SPECS[self.weapon][self.size]['power'])


POINT_DEFENSE_SPECS: dict[PointDefenseKind, dict[PointDefenseRating, dict[str, float | int | str]]] = {
    'laser': {
        1: {'item': 'Point Defense Battery: Type I-L', 'minimum_tl': 10, 'power': 10, 'tons': 20, 'cost': 5_000_000},
        2: {'item': 'Point Defense Battery: Type II-L', 'minimum_tl': 12, 'power': 20, 'tons': 20, 'cost': 10_000_000},
        3: {'item': 'Point Defense Battery: Type III-L', 'minimum_tl': 14, 'power': 30, 'tons': 20, 'cost': 20_000_000},
    },
    'gauss': {
        1: {'item': 'Point Defense Battery: Type I-G', 'minimum_tl': 10, 'power': 5, 'tons': 20, 'cost': 3_000_000},
        2: {'item': 'Point Defense Battery: Type II-G', 'minimum_tl': 12, 'power': 15, 'tons': 20, 'cost': 6_000_000},
        3: {'item': 'Point Defense Battery: Type III-G', 'minimum_tl': 14, 'power': 25, 'tons': 20, 'cost': 10_000_000},
    },
}


class PointDefenseBattery(ShipPart):
    kind: PointDefenseKind
    rating: PointDefenseRating

    def build_item(self) -> str | None:
        return str(POINT_DEFENSE_SPECS[self.kind][self.rating]['item'])

    def build_notes(self) -> list[Note]:
        intercept_dice = self.rating * 2
        notes = [Note(category=NoteCategory.INFO, message=f'Intercept +{intercept_dice}D')]
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
        return int(POINT_DEFENSE_SPECS[self.kind][self.rating]['minimum_tl'])

    @property
    def hardpoints_required(self) -> int:
        return 1

    def compute_tons(self) -> float:
        return float(POINT_DEFENSE_SPECS[self.kind][self.rating]['tons'])

    def compute_cost(self) -> float:
        return float(POINT_DEFENSE_SPECS[self.kind][self.rating]['cost'])

    def compute_power(self) -> float:
        return float(POINT_DEFENSE_SPECS[self.kind][self.rating]['power'])


ShipTurret = Annotated[SingleTurret | DoubleTurret | TripleTurret, Field(discriminator='mount_type')]


class WeaponsSection(CeresModel):
    turrets: list[ShipTurret] = Field(default_factory=list)
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
                if isinstance(turret, SingleTurret):
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
        for turret in self.turrets:
            spec.add_row(ship._spec_row_for_part(SpecSection.WEAPONS, turret))
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

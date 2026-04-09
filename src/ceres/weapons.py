import math
from typing import Annotated, ClassVar, Literal

from pydantic import Field

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


class FixedFirmpoint(ShipPart):
    mount_cost: ClassVar[int] = 100_000
    minimum_tl = 9
    weapon: PulseLaser

    def build_item(self) -> str | None:
        return self.weapon.build_item()

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return self.mount_cost + self.weapon.weapon_cost

    def compute_power(self) -> float:
        power = self.weapon.weapon_power
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


ShipTurret = Annotated[SingleTurret | DoubleTurret | TripleTurret, Field(discriminator='mount_type')]


class WeaponsSection(CeresModel):
    turrets: list[ShipTurret] = Field(default_factory=list)
    fixed_firmpoints: list[FixedFirmpoint] = Field(default_factory=list)
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
        total_mounts = len(self.turrets) + len(self.fixed_firmpoints)
        capacity = self.mount_capacity(ship)
        if total_mounts > capacity:
            overflow = total_mounts - capacity
            overflowing_parts = [*self.fixed_firmpoints, *self.turrets][-overflow:]
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

    def _all_parts(self) -> list[ShipPart]:
        parts: list[ShipPart] = [*self.turrets, *self.fixed_firmpoints]
        if self.missile_storage is not None:
            parts.append(self.missile_storage)
        return parts

    def add_spec_rows(self, ship, spec: ShipSpec) -> None:
        for turret in self.turrets:
            spec.add_row(ship._spec_row_for_part(SpecSection.WEAPONS, turret))
        for row in ship._grouped_spec_rows(SpecSection.WEAPONS, self.fixed_firmpoints):
            spec.add_row(row)
        if self.missile_storage is not None:
            spec.add_row(ship._spec_row_for_part(SpecSection.WEAPONS, self.missile_storage))

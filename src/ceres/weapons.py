import math
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from .base import CeresModel, Note, NoteCategory
from .parts import ShipPart
from .spec import ShipSpec, SpecSection


class PulseLaser(CeresModel):
    """Pulse laser weapon (TL9, 2D damage, Long range)."""

    model_config = {'frozen': True}
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


class FixedFirmpoint(ShipPart):
    mount_cost: ClassVar[int] = 100_000
    minimum_tl = 9
    weapon: PulseLaser

    def build_item(self) -> str | None:
        return self.weapon.build_item()

    def compute_tons(self) -> float:
        return 0.0

    def compute_cost(self) -> float:
        return self.mount_cost + self.weapon.base_cost * self.weapon.cost_modifier

    def compute_power(self) -> float:
        power = self.weapon.base_power
        if self.weapon.energy_efficient:
            power *= 0.75
        # Firmpoint reduces power by 25%; apply combined then floor
        power *= 0.75
        return float(math.floor(power))


class DoubleTurret(ShipPart):
    mount_type: Literal['double'] = 'double'
    minimum_tl = 8

    def build_item(self) -> str | None:
        return 'Double Turret'

    def build_notes(self) -> list[Note]:
        return [Note(category=NoteCategory.INFO, message='No weapons in turret')]

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 500_000.0

    def compute_power(self) -> float:
        return 1.0


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


TurretWeapon = Annotated[TurretBeamLaser | TurretMissileRack, Field(discriminator='weapon_type')]


class TripleTurret(ShipPart):
    mount_type: Literal['triple'] = 'triple'
    minimum_tl = 9
    weapons: list[TurretWeapon] = Field(default_factory=list)

    def build_item(self) -> str | None:
        return 'Triple Turret'

    def build_notes(self) -> list[Note]:
        if not self.weapons:
            return [Note(category=NoteCategory.INFO, message='No weapons in turret')]
        return [Note(category=NoteCategory.INFO, message=w.build_item() or w.__class__.__name__) for w in self.weapons]

    def compute_tons(self) -> float:
        return 1.0

    def compute_cost(self) -> float:
        return 1_000_000.0 + sum(w.weapon_cost for w in self.weapons)

    def compute_power(self) -> float:
        return 1.0 + sum(w.weapon_power for w in self.weapons)


class MissileStorage(ShipPart):
    """Magazine for missiles: 12 missiles per ton, no cost."""

    count: int

    def build_item(self) -> str | None:
        return f'Missile Storage ({self.count})'

    def compute_tons(self) -> float:
        return self.count / 12

    def compute_cost(self) -> float:
        return 0.0


ShipTurret = Annotated[DoubleTurret | TripleTurret, Field(discriminator='mount_type')]


class WeaponsSection(CeresModel):
    turrets: list[ShipTurret] = Field(default_factory=list)
    fixed_firmpoints: list[FixedFirmpoint] = Field(default_factory=list)
    missile_storage: MissileStorage | None = None

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

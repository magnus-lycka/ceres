import math
from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import NoteList, _Note

from ..parts import ShipPart
from ..storage import CargoHold


class _SpinalMount(ShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
    spinal_type: str
    size_multiple: int = Field(default=1, ge=1)
    tl_improvement: Literal[0, 1, 2, 3] = 0
    description: ClassVar[str]
    base_tons: ClassVar[float]
    base_power: ClassVar[float]
    base_cost: ClassVar[float]
    base_damage_dice: ClassVar[int]
    max_tons: ClassVar[float]
    traits: ClassVar[tuple[str, ...]] = ()
    extra_info_notes: ClassVar[tuple[str, ...]] = ()

    _tons_multipliers: ClassVar[dict[int, float]] = {0: 1.0, 1: 0.9, 2: 0.85, 3: 0.8}
    _cost_multipliers: ClassVar[dict[int, float]] = {0: 1.0, 1: 1.1, 2: 1.2, 3: 1.3}

    def bind(self, assembly) -> None:
        super().bind(assembly)
        if self.tons > self.max_tons:
            self.error(f'{self.description} exceeds maximum size of {self.max_tons:g} tons')
        if self.tons > assembly.displacement / 2:
            self.error('Spinal mount cannot exceed half the ship displacement')

    def check_tl(self) -> None:
        required_tl = self.tl + self.tl_improvement
        if self.assembly_tl < required_tl:
            self.error(f'Requires TL{required_tl}, ship is TL{self.assembly_tl}')

    def item_description(self) -> str:
        if self.tl_improvement:
            return f'{self.description} (TL{self.tl + self.tl_improvement})'
        return self.description

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        notes.info(f'Damage: {self.base_damage_dice * self.size_multiple}D × 1,000')
        if self.traits:
            notes.info(f'Traits: {", ".join(self.traits)}')
        for message in self.extra_info_notes:
            notes.info(message)
        return notes

    @property
    def hardpoints_required(self) -> int:
        return math.ceil(self.tons / 100)

    @property
    def crew_required_commercial(self) -> int:
        return 0

    @property
    def crew_required_military(self) -> int:
        return math.ceil(self.tons / 100)

    @property
    def tons(self) -> float:
        return self.base_tons * self.size_multiple * self._tons_multipliers[self.tl_improvement]

    @property
    def cost(self) -> float:
        return self.base_cost * self.size_multiple * self._cost_multipliers[self.tl_improvement]

    @property
    def power(self) -> float:
        return self.base_power * self.size_multiple


class MassDriverSpinalMount(_SpinalMount):
    spinal_type: Literal['mass_driver_spinal_mount'] = 'mass_driver_spinal_mount'
    description = 'Mass Driver Spinal Mount'
    tl: int = 10
    base_tons = 5_000.0
    base_power = 250.0
    base_cost = 1_500_000_000.0
    base_damage_dice = 4
    max_tons = 100_000.0
    traits = ('AP 15', 'Orbital Bombardment')
    extra_info_notes = ('Ammunition is 50 tons and Cr500,000 per attack',)

    @staticmethod
    def ammunition_cargo(attacks: int = 1) -> CargoHold:
        if attacks < 1:
            raise ValueError('Mass driver spinal mount ammunition must cover at least one attack')
        label = 'Mass Driver Spinal Mount Ammunition'
        attack_label = 'attack' if attacks == 1 else 'attacks'
        return CargoHold(
            tons=50.0 * attacks,
            cost=500_000.0 * attacks,
            display_label=f'{label} ({attacks} {attack_label})',
        )


class MesonSpinalMount(_SpinalMount):
    spinal_type: Literal['meson_spinal_mount'] = 'meson_spinal_mount'
    description = 'Meson Spinal Mount'
    tl: int = 12
    base_tons = 7_500.0
    base_power = 1_000.0
    base_cost = 2_000_000_000.0
    base_damage_dice = 6
    max_tons = 75_000.0
    traits = ('AP ∞', 'Radiation')
    extra_info_notes = ('Meson spinal mounts ignore all armour and radiation shielding',)


class ParticleAcceleratorSpinalMount(_SpinalMount):
    spinal_type: Literal['particle_accelerator_spinal_mount'] = 'particle_accelerator_spinal_mount'
    description = 'Particle Accelerator Spinal Mount'
    tl: int = 11
    base_tons = 3_500.0
    base_power = 1_000.0
    base_cost = 1_000_000_000.0
    base_damage_dice = 8
    max_tons = 28_000.0
    traits = ('Radiation',)
    extra_info_notes = ('Damage is reduced by 3% per point of target armour before applying the damage multiple',)


class RailgunSpinalMount(_SpinalMount):
    spinal_type: Literal['railgun_spinal_mount'] = 'railgun_spinal_mount'
    description = 'Railgun Spinal Mount'
    tl: int = 10
    base_tons = 3_500.0
    base_power = 500.0
    base_cost = 500_000_000.0
    base_damage_dice = 4
    max_tons = 21_000.0
    traits = ('AP 20',)
    extra_info_notes = (
        'Damage is reduced by 2% per point of target armour before applying the damage multiple',
        'Includes five rounds; extra railgun rounds are 20 tons and MCr0.2 each',
    )

    @staticmethod
    def extra_rounds_cargo(rounds: int = 1) -> CargoHold:
        if rounds < 1:
            raise ValueError('Railgun spinal mount ammunition must include at least one extra round')
        round_label = 'round' if rounds == 1 else 'rounds'
        return CargoHold(
            tons=20.0 * rounds,
            cost=200_000.0 * rounds,
            display_label=f'Railgun Spinal Mount Extra Rounds ({rounds} {round_label})',
        )


type SpinalMount = Annotated[
    MassDriverSpinalMount | MesonSpinalMount | ParticleAcceleratorSpinalMount | RailgunSpinalMount,
    Field(discriminator='spinal_type'),
]

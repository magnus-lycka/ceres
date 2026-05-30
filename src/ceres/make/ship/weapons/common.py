from collections.abc import Sequence
from typing import Annotated, ClassVar, Literal

from pydantic import ConfigDict, Field

from ceres.shared import CeresModel, NoteList, _Note

from ..parts import (
    CustomisationUnion,
    EnergyEfficient,
    Modification,
)
from ..text import format_counted_label

LongRange = Modification(
    name='Long Range',
    advantage=2,
    info_notes=('Range increased by one band, to a maximum of Very Long',),
)

HighYield = Modification(name='High Yield', advantage=1)

VeryHighYield = Modification(name='Very High Yield', advantage=2)

Accurate = Modification(
    name='Accurate',
    advantage=2,
    info_notes=('Accurate weapons gain DM+1 to attack rolls',),
)

EasyToRepair = Modification(
    name='Easy to Repair',
    advantage=1,
    info_notes=('Easy to Repair weapons grant DM+1 to repair attempts',),
)

Resilient = Modification(
    name='Resilient',
    advantage=1,
    info_notes=('Resilient weapons reduce weapon critical hit Severity by -1',),
)

Inaccurate = Modification(
    name='Inaccurate',
    disadvantage=1,
    info_notes=('Inaccurate weapons suffer DM-1 to attack rolls',),
)

IntenseFocus = Modification(
    name='Intense Focus',
    advantage=2,
    info_notes=('Intense Focus weapons gain AP+2',),
)

_GENERAL_WEAPON_MODIFICATIONS = frozenset(
    {
        Accurate.name,
        EasyToRepair.name,
        EnergyEfficient.name,
        HighYield.name,
        Inaccurate.name,
        IntenseFocus.name,
        LongRange.name,
        Resilient.name,
        VeryHighYield.name,
    }
)

_INTENSE_FOCUS_WEAPONS = frozenset({'beam_laser', 'particle', 'particle_beam', 'pulse_laser'})


def _check_intense_focus(notes: NoteList, customisation: CustomisationUnion | None, weapon: str) -> None:
    if customisation is None:
        return
    if weapon in _INTENSE_FOCUS_WEAPONS:
        return
    for mod in customisation.modifications:
        if mod.name == IntenseFocus.name:
            notes.error('Intense Focus is only applicable for laser and particle weapons')


def _size_reduction_steps(value: bool | int) -> int:
    return 1 if value is True else int(value)


def _damage_multiple_text(multiplier: int | None) -> str | None:
    if multiplier is None:
        return None
    return f'Damage × {multiplier} after armour'


def _mounted_weapon_label(weapon: MountWeapon) -> str:
    return weapon.build_item() or weapon.__class__.__name__


def _mounted_weapon_notes(weapons: Sequence[MountWeapon], *, empty_message: str) -> list[_Note]:
    if not weapons:
        notes = NoteList()
        notes.info(empty_message)
        return notes
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

    notes = NoteList()
    for item, customisation in order:
        notes.content(format_counted_label(item, groups[(item, customisation)]))
        if customisation is not None:
            notes.info(customisation)
    return notes


def _mounted_weapon_cost(weapons: Sequence[MountWeapon]) -> float:
    return sum(w.weapon_cost for w in weapons)


def _mounted_weapon_power(weapons: Sequence[MountWeapon]) -> float:
    return sum(w.weapon_power for w in weapons)


class _MountWeapon(CeresModel):
    notes: ClassVar[NoteList]
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)
    weapon_type: str
    description: ClassVar[str]
    base_cost: ClassVar[float]
    base_power: ClassVar[float]
    high_yield_allowed: ClassVar[bool] = True
    customisation: CustomisationUnion | None = None
    allowed_modifications: ClassVar[frozenset[str]] = _GENERAL_WEAPON_MODIFICATIONS

    @property
    def notes(self) -> NoteList:
        notes = NoteList()
        if message := self.build_item():
            notes.item(message)
        if self.customisation is not None:
            for mod in self.customisation.modifications:
                if mod.name not in self.allowed_modifications:
                    notes.error(f'Modification not allowed for MountWeapon: {mod.name}')
            _check_intense_focus(notes, self.customisation, self.weapon_type)
            notes.extend(self.customisation.notes)

            if not self.high_yield_allowed:
                for mod in self.customisation.modifications:
                    if mod.name in {HighYield.name, VeryHighYield.name}:
                        notes.error(f'{mod.name} is not applicable for {self.build_item()}')
            for mod in self.customisation.modifications:
                notes.extend(mod.build_notes())
        return notes

    def customisation_note(self) -> _Note | None:
        if self.customisation is None:
            return None
        notes = NoteList()
        notes.info(self.customisation.note_text)
        return notes[0]

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
    description = 'Pulse Laser'
    base_cost = 1_000_000.0
    base_power = 4.0


class BeamLaser(_MountWeapon):
    weapon_type: Literal['beam_laser'] = 'beam_laser'
    description = 'Beam Laser'
    base_cost = 500_000.0
    base_power = 4.0


class FusionGun(_MountWeapon):
    weapon_type: Literal['fusion_gun'] = 'fusion_gun'
    description = 'Fusion Gun'
    base_cost = 2_000_000.0
    base_power = 12.0


class LaserDrill(_MountWeapon):
    weapon_type: Literal['laser_drill'] = 'laser_drill'
    description = 'Laser Drill'
    base_cost = 150_000.0
    base_power = 4.0


class MissileRack(_MountWeapon):
    weapon_type: Literal['missile_rack'] = 'missile_rack'
    description = 'Missile Rack'
    base_cost = 750_000.0
    base_power = 0.0
    high_yield_allowed = False


class ParticleBeam(_MountWeapon):
    weapon_type: Literal['particle_beam'] = 'particle_beam'
    description = 'Particle Beam'
    base_cost = 4_000_000.0
    base_power = 8.0


class PlasmaGun(_MountWeapon):
    weapon_type: Literal['plasma_gun'] = 'plasma_gun'
    description = 'Plasma Gun'
    base_cost = 2_500_000.0
    base_power = 6.0


class Sandcaster(_MountWeapon):
    weapon_type: Literal['sandcaster'] = 'sandcaster'
    description = 'Sandcaster'
    base_cost = 250_000.0
    base_power = 0.0


class Railgun(_MountWeapon):
    weapon_type: Literal['railgun'] = 'railgun'
    description = 'Railgun'
    base_cost = 1_000_000.0
    base_power = 2.0


type MountWeapon = Annotated[
    PulseLaser | BeamLaser | FusionGun | LaserDrill | MissileRack | ParticleBeam | PlasmaGun | Railgun | Sandcaster,
    Field(discriminator='weapon_type'),
]

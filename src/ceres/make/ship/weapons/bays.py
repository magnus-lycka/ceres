from typing import Annotated, ClassVar, Literal

from pydantic import Field

from ceres.shared import NoteList, _Note

from ..parts import CustomisableShipPart, ShipPart, SizeReduction
from .common import (
    _GENERAL_WEAPON_MODIFICATIONS,
    HighYield,
    VeryHighYield,
    _check_intense_focus,
    _damage_multiple_text,
)

BaySize = Literal['small', 'medium', 'large']
BayWeapon = Literal[
    'fusion_gun',
    'hullcutter',
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


class _Bay(CustomisableShipPart):
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]
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
    allowed_modifications: ClassVar[frozenset[str]] = _GENERAL_WEAPON_MODIFICATIONS | {SizeReduction.name}

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        if self.customisation is None:
            return
        if self.weapon in {'missile', 'torpedo'}:
            for mod in self.customisation.modifications:
                if mod.name in {HighYield.name, VeryHighYield.name}:
                    self.error(f'{mod.name} is not applicable for {self.build_item()}')

    def item_description(self) -> str:
        item = f'{self.size.title()} {self.weapon_label} Bay'
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

    def build_notes(self) -> list[_Note]:
        notes = NoteList(ShipPart.build_notes(self))
        if self.magazine_summary is not None:
            notes.info(self.magazine_summary)
        if self.customisation is not None:
            _check_intense_focus(notes, self.customisation, self.weapon)
            notes.info(self.customisation.note_text)
            for mod in self.customisation.modifications:
                notes.extend(mod.build_notes())
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

    @property
    def tons(self) -> float:
        return self.base_tons * self.tons_multiplier

    @property
    def cost(self) -> float:
        return self.base_cost * self.cost_multiplier

    @property
    def power(self) -> float:
        return self.base_power * self.power_multiplier


class _Carronade(ShipPart):
    carronade_type: str
    description: ClassVar[str]
    damage: ClassVar[str]
    traits: ClassVar[tuple[str, ...]] = ('Weak',)
    base_cost: ClassVar[float]
    base_power: ClassVar[float]
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def hardpoints_required(self) -> int:
        return 4

    @property
    def crew_required_commercial(self) -> int:
        return 0

    @property
    def crew_required_military(self) -> int:
        return 1

    @property
    def tons(self) -> float:
        return 4.0

    @property
    def cost(self) -> float:
        return self.base_cost

    @property
    def power(self) -> float:
        return self.base_power

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        trait_text = ', '.join(self.traits)
        notes.info(f'Damage: {self.damage}; {trait_text} trait doubles target armour against damage')
        return notes


class PlasmaCarronade(_Carronade):
    carronade_type: Literal['plasma_carronade'] = 'plasma_carronade'
    description = 'Plasma Carronade'
    tl: int = 10
    damage = '12D'
    base_power = 35.0
    base_cost = 10_000_000.0


class FusionCarronade(_Carronade):
    carronade_type: Literal['fusion_carronade'] = 'fusion_carronade'
    description = 'Fusion Carronade'
    tl: int = 12
    damage = '16D'
    traits = ('Radiation', 'Weak')
    base_power = 45.0
    base_cost = 12_000_000.0


type Carronade = Annotated[
    PlasmaCarronade | FusionCarronade,
    Field(discriminator='carronade_type'),
]


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


class LargeHullcutterBay(_LargeBay):
    bay_type: Literal['large_hullcutter_bay'] = 'large_hullcutter_bay'
    weapon: ClassVar[BayWeapon] = 'hullcutter'
    weapon_label = 'Hullcutter'
    tl: int = 16
    base_power = 100.0
    base_cost = 110_000_000.0
    damage_multiplier: ClassVar[int | None] = None

    def build_notes(self) -> list[_Note]:
        notes = NoteList(super().build_notes())
        notes.info('Reductor: target armour is reduced by -1 per damage die before damage is applied')
        return notes


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


class GeneralPurposeMassDriverBay(ShipPart):
    bay_type: Literal['general_purpose_mass_driver_bay'] = 'general_purpose_mass_driver_bay'
    description: Literal['Small General-Purpose Mass Driver Bay'] = 'Small General-Purpose Mass Driver Bay'
    tl: int = 8
    extra_launch_capacity: float = 0.0
    tons: ClassVar[float]
    cost: ClassVar[float]
    power: ClassVar[float]

    @property
    def hardpoints_required(self) -> int:
        return 1

    @property
    def crew_required_commercial(self) -> int:
        return 0

    @property
    def crew_required_military(self) -> int:
        return 1

    @property
    def launch_capacity(self) -> float:
        return 50.0 + self.extra_launch_capacity

    @property
    def tons(self) -> float:
        return 50.0 + 2.0 * self.extra_launch_capacity

    @property
    def cost(self) -> float:
        return 4_000_000.0 + 75_000.0 * self.extra_launch_capacity

    @property
    def power(self) -> float:
        return 10.0 + 3.0 * self.extra_launch_capacity

    def build_notes(self) -> list[_Note]:
        notes = NoteList()
        notes.info(f'Can launch {self.launch_capacity:g} tons; DM-4 to attack rolls against manoeuvring targets')
        return notes


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
    | LargeHullcutterBay
    | SmallIonCannonBay
    | MediumIonCannonBay
    | LargeIonCannonBay
    | SmallMassDriverBay
    | MediumMassDriverBay
    | LargeMassDriverBay
    | GeneralPurposeMassDriverBay
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

"""Approval snapshots for ship weapons.

Snapshot 1 (test_mount_weapon_table): all HG turret weapon base values + key customisations.
Snapshot 2 (test_spinal_mount_table): all 4 spinal types — base values and TL improvement scaling.
Snapshot 3 (test_bays_carronades_point_defense): bay weapons, carronades, and point defense batteries.
Snapshot 4 (test_weapon_mount_types): turret types, fixed mounts, barbettes, and their spec rows.
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive1, PowerSection
from ceres.make.ship.parts import Advanced, Budget, EnergyEfficient, HighTechnology, SizeReduction, VeryAdvanced
from ceres.make.ship.weapons import (
    Accurate,
    BeamLaser,
    DoubleTurret,
    EasyToRepair,
    FixedMount,
    FusionCarronade,
    FusionGun,
    GaussPointDefenseBattery3,
    GeneralPurposeMassDriverBay,
    HighYield,
    Inaccurate,
    IntenseFocus,
    LargeHullcutterBay,
    LargeMesonGunBay,
    LargeTorpedoBay,
    LaserDrill,
    LaserPointDefenseBattery2,
    MassDriverSpinalMount,
    MediumMissileBay,
    MediumParticleBeamBay,
    MesonSpinalMount,
    MissileRack,
    ParticleAcceleratorSpinalMount,
    ParticleBarbette,
    ParticleBeam,
    PlasmaBarbette,
    PlasmaCarronade,
    PlasmaGun,
    PulseLaser,
    PulseLaserBarbette,
    QuadTurret,
    Railgun,
    RailgunSpinalMount,
    Resilient,
    Sandcaster,
    SingleTurret,
    SmallMissileBay,
    TorpedoBarbette,
    TorpedoInterceptorCluster,
    TripleTurret,
    VeryHighYield,
    WeaponsSection,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=1_000):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=1_000):
    part.bind(_Ship(tl, displacement))
    return part


@pytest.mark.approval
def test_mount_weapon_table(snapshot):
    """All HG turret weapons — base weapon_cost, weapon_power, build_item and key customisation effects."""
    snap = AnnotatedSnapshot(
        {
            'BeamLaser': {
                'cost': BeamLaser().weapon_cost,
                'power': BeamLaser().weapon_power,
                'item': BeamLaser().build_item(),
            },
            'FusionGun': {
                'cost': FusionGun().weapon_cost,
                'power': FusionGun().weapon_power,
                'item': FusionGun().build_item(),
            },
            'LaserDrill': {
                'cost': LaserDrill().weapon_cost,
                'power': LaserDrill().weapon_power,
                'item': LaserDrill().build_item(),
            },
            'MissileRack': {
                'cost': MissileRack().weapon_cost,
                'power': MissileRack().weapon_power,
                'item': MissileRack().build_item(),
            },
            'ParticleBeam': {
                'cost': ParticleBeam().weapon_cost,
                'power': ParticleBeam().weapon_power,
                'item': ParticleBeam().build_item(),
            },
            'PlasmaGun': {
                'cost': PlasmaGun().weapon_cost,
                'power': PlasmaGun().weapon_power,
                'item': PlasmaGun().build_item(),
            },
            'PulseLaser': {
                'cost': PulseLaser().weapon_cost,
                'power': PulseLaser().weapon_power,
                'item': PulseLaser().build_item(),
            },
            'Railgun': {'cost': Railgun().weapon_cost, 'power': Railgun().weapon_power, 'item': Railgun().build_item()},
            'Sandcaster': {
                'cost': Sandcaster().weapon_cost,
                'power': Sandcaster().weapon_power,
                'item': Sandcaster().build_item(),
            },
        }
    )
    snap.annotate(
        'advanced_energy_efficient_cost_modifier',
        str(PulseLaser(customisation=Advanced(modifications=[EnergyEfficient])).cost_modifier),
    )
    snap.annotate(
        'very_advanced_very_high_yield_cost_modifier',
        str(PulseLaser(customisation=VeryAdvanced(modifications=[VeryHighYield])).cost_modifier),
    )
    snap.annotate(
        'high_technology_vhy_ee_cost_modifier',
        str(PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient])).cost_modifier),
    )
    snap.annotate(
        'budget_inaccurate_cost_modifier',
        str(PulseLaser(customisation=Budget(modifications=[Inaccurate])).cost_modifier),
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_spinal_mount_table(snapshot):
    """All 4 spinal mount types — base values (size_multiple=1) and TL improvement scaling."""

    def _spinal_row(spinal_cls, tl, tl_improvement=0, size_multiple=1, displacement=200_000):
        s = spinal_cls(tl_improvement=tl_improvement, size_multiple=size_multiple)
        s.bind(_Ship(tl, displacement))
        return {
            'tl': s.tl,
            'tons': round(float(s.tons), 1),
            'power': round(float(s.power), 1),
            'cost': round(float(s.cost), 0),
            'max_tons': round(float(s.max_tons), 0),
            'hardpoints': s.hardpoints_required,
        }

    snap = AnnotatedSnapshot(
        {
            'MassDriverSpinalMount': _spinal_row(MassDriverSpinalMount, 10),
            'MesonSpinalMount': _spinal_row(MesonSpinalMount, 12),
            'ParticleAcceleratorSpinalMount': _spinal_row(ParticleAcceleratorSpinalMount, 11),
            'RailgunSpinalMount': _spinal_row(RailgunSpinalMount, 10),
            'ParticleAccelerator_size2': _spinal_row(
                ParticleAcceleratorSpinalMount, 11, size_multiple=2, displacement=50_000
            ),
            'MesonSpinalMount_tl_improvement_1': _spinal_row(MesonSpinalMount, 13, tl_improvement=1),
            'MesonSpinalMount_tl_improvement_3': _spinal_row(MesonSpinalMount, 15, tl_improvement=3),
        }
    )
    snap.annotate(
        'pa_size2_damage_info',
        str(
            'Damage: 16D × 1,000'
            in _bind(ParticleAcceleratorSpinalMount(size_multiple=2), tl=11, displacement=50_000).notes.infos
        ),
    )
    snap.annotate('mass_driver_ammo_cargo_3attacks_tons', str(MassDriverSpinalMount.ammunition_cargo(attacks=3).tons))
    snap.annotate('railgun_extra_rounds_6_tons', str(RailgunSpinalMount.extra_rounds_cargo(rounds=6).tons))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_bays_carronades_point_defense(snapshot):
    """Bay weapons, carronades, and point defense batteries — table values + spec rows."""

    def _bay_row(bay, tl=12, displacement=1_000):
        b = bay
        b.bind(_Ship(tl, displacement))
        return {
            'tons': round(float(b.tons), 1),
            'cost': round(float(b.cost), 0),
            'power': round(float(b.power), 1),
            'hardpoints': b.hardpoints_required,
        }

    gpmdb = GeneralPurposeMassDriverBay(extra_launch_capacity=3)
    gpmdb.bind(_Ship(8))

    snap = AnnotatedSnapshot(
        {
            'SmallMissileBay': _bay_row(SmallMissileBay()),
            'SmallMissileBay_size_reduction': _bay_row(
                SmallMissileBay(customisation=Advanced(modifications=[SizeReduction])), 13
            ),
            'MediumMissileBay': _bay_row(MediumMissileBay(), 10),
            'MediumParticleBeamBay': _bay_row(MediumParticleBeamBay()),
            'MediumParticleBeamBay_hy_2sr': _bay_row(
                MediumParticleBeamBay(
                    customisation=HighTechnology(modifications=[HighYield, SizeReduction, SizeReduction])
                ),
                15,
            ),
            'LargeTorpedoBay': _bay_row(LargeTorpedoBay()),
            'LargeHullcutterBay': _bay_row(LargeHullcutterBay(), 16, 10_000),
            'LargeMesonGunBay': _bay_row(LargeMesonGunBay(), 16, 10_000),
            'GeneralPurposeMassDriverBay_extra3': {
                'tons': round(float(gpmdb.tons), 1),
                'cost': round(float(gpmdb.cost), 0),
                'power': round(float(gpmdb.power), 1),
                'launch_capacity': round(float(gpmdb.launch_capacity), 1),
            },
            'PlasmaCarronade': _bay_row(PlasmaCarronade(), 10),
            'FusionCarronade': _bay_row(FusionCarronade()),
            'LaserPointDefenseBattery2': _bay_row(LaserPointDefenseBattery2()),
            'GaussPointDefenseBattery3': _bay_row(GaussPointDefenseBattery3(), 12),
            'TorpedoInterceptorCluster': _bay_row(TorpedoInterceptorCluster(), 10),
        }
    )
    snap.annotate('hullcutter_infos', str(_bind(LargeHullcutterBay(), 16, 10_000).notes.infos))
    snap.annotate('carronade_plasma_infos', str(_bind(PlasmaCarronade(), 10).notes.infos))
    snap.annotate('torpedo_interceptor_infos', str(_bind(TorpedoInterceptorCluster(), 10).notes.infos))
    snap.annotate('gpmdb_infos', str(gpmdb.notes.infos))
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_weapon_mount_types(snapshot):
    """Turret types, fixed mounts, and barbettes — cost, power, and spec row behaviour."""

    def _turret(cls, weapons, tl=12, displacement=100):
        t = cls(weapons=weapons)
        t.bind(_Ship(tl, displacement))
        return {'tons': round(float(t.tons), 2), 'cost': round(float(t.cost), 0), 'power': round(float(t.power), 2)}

    # FixedMount: firmpoint reduces power by 25%
    fp_base = FixedMount(weapons=[PulseLaser()])
    fp_base.bind(_Ship(12, 6))
    fp_ht = FixedMount(
        weapons=[PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))]
    )
    fp_ht.bind(_Ship(12, 6))

    pb = _bind(PulseLaserBarbette(), 12, 200)
    particle_b = _bind(ParticleBarbette(), 13, 400)
    torpedo_b = _bind(TorpedoBarbette(), 12, 400)
    plasma_b = _bind(PlasmaBarbette(), 10, 400)

    turret_ship = ship.Ship(
        tl=15,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(plant=FusionPlantTL12(output=50)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        weapons=WeaponsSection(
            turrets=[
                TripleTurret(weapons=[PulseLaser(), PulseLaser(), PulseLaser()]),
                TripleTurret(weapons=[PulseLaser(), PulseLaser(), PulseLaser()]),
            ]
        ),
    )
    turret_row = turret_ship.build_spec().row('Triple Turret', section='Weapons')

    snap = AnnotatedSnapshot(
        {
            'FixedMount_base': {
                'tons': float(fp_base.tons),
                'cost': float(fp_base.cost),
                'power': float(fp_base.power),
            },
            'FixedMount_ht_vhy_ee': {'tons': float(fp_ht.tons), 'cost': float(fp_ht.cost), 'power': float(fp_ht.power)},
            'SingleTurret': _turret(SingleTurret, [PulseLaser()]),
            'DoubleTurret': _turret(DoubleTurret, [PulseLaser(), Sandcaster()]),
            'TripleTurret': _turret(TripleTurret, [PulseLaser(), MissileRack(), Sandcaster()]),
            'QuadTurret': _turret(QuadTurret, [PulseLaser(), PulseLaser(), MissileRack(), Sandcaster()]),
            'PulseLaserBarbette': {'tons': float(pb.tons), 'cost': float(pb.cost), 'power': float(pb.power)},
            'ParticleBarbette': {
                'tons': float(particle_b.tons),
                'cost': float(particle_b.cost),
                'power': float(particle_b.power),
            },
            'TorpedoBarbette': {'tons': float(torpedo_b.tons), 'cost': float(torpedo_b.cost)},
            'PlasmaBarbette': {
                'tons': float(plasma_b.tons),
                'cost': float(plasma_b.cost),
                'power': float(plasma_b.power),
            },
            'triple_turret_spec_row_quantity': turret_row.quantity,
            'triple_turret_spec_row_tons': turret_row.tons,
            'triple_turret_spec_row_cost': turret_row.cost,
        }
    )
    snap.annotate('particle_barbette_item', str(particle_b.build_item()))
    snap.annotate('torpedo_barbette_crew_commercial', str(torpedo_b.crew_required_commercial))
    snap.annotate('torpedo_barbette_crew_military', str(torpedo_b.crew_required_military))
    snap.annotate('accurate_notes', str(PulseLaser(customisation=VeryAdvanced(modifications=[Accurate])).notes.infos))
    snap.annotate(
        'intense_focus_notes', str(PulseLaser(customisation=VeryAdvanced(modifications=[IntenseFocus])).notes.infos)
    )
    snap.annotate(
        'easy_to_repair_resilient_notes',
        str(BeamLaser(customisation=VeryAdvanced(modifications=[EasyToRepair, Resilient])).notes.infos),
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

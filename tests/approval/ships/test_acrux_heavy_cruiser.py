"""Approval snapshot for Spinward Extents Acrux-class Heavy Cruiser.

The source image header says `Acrux Heavy Cruiser`, while the class ribbon says
`Class: Heavy Scout`. The latter is retained here as a source value but treated
as a likely layout/copy error until a text source confirms otherwise.

This is a capstone validation case that is intentionally being made buildable
one subsystem at a time. It exercises several systems that are not fully
modelled yet, including command bridges at capital-ship scale and large craft
berthing.
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import ComputerSection, Core50, Core60
from ceres.make.ship.crafts import CraftSection, EmptyOccupant, FullHangar, InternalDockingSpace
from ceres.make.ship.drives import DriveSection, FusionPlantTL8, JDrive2, MDrive5, PowerSection
from ceres.make.ship.habitation import Barracks, Brig, HabitationSection, HighStateroom, LowBerth, Stateroom
from ceres.make.ship.parts import HighTechnology, SizeReduction, VeryAdvanced
from ceres.make.ship.sensors import ExtendedArrays, MilitarySensors, SensorsSection
from ceres.make.ship.software import (
    AdvancedFireControl,
    AntiHijack,
    AutoRepair,
    BattleSystem,
    ElectronicWarfare,
    Evade,
    LaunchSolution,
    VirtualCrew,
)
from ceres.make.ship.storage import (
    CargoCrane,
    CargoHold,
    CargoSection,
    FuelProcessor,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import (
    Armoury,
    BriefingRoom,
    CommonArea,
    MedicalBay,
    RepairDrones,
    SystemsSection,
    TrainingFacility,
    UNREPSystem,
    Workshop,
)
from ceres.make.ship.weapons import (
    BeamLaser,
    LargeMissileBay,
    LargeTorpedoBay,
    LaserPointDefenseBattery1,
    LongRange,
    MediumParticleBeamBay,
    MissileStorage,
    ParticleAcceleratorSpinalMount,
    ParticleBarbette,
    PlasmaBarbette,
    PulseLaser,
    Sandcaster,
    SandcasterCanisterStorage,
    TorpedoStorage,
    TripleTurret,
    WeaponsSection,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def _size_reduction(steps: int):
    if steps == 2:
        return VeryAdvanced(modifications=[SizeReduction, SizeReduction])
    if steps == 3:
        return HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction])
    raise ValueError(f'Acrux only uses size reduction x2/x3, got x{steps}')


def build_acrux_heavy_cruiser() -> ship.Ship:
    """Note: Partial Acrux Heavy Cruiser — source snapshot still has unresolved modelling work.

    The command bridge source row is not the same part as the Ceres High Guard
    CommandBridge system. Armour tonnage is matched to the Spinward Extents
    source snapshot, while armour cost is still not traced to an HG rule.
    """
    pulse_long_range = VeryAdvanced(modifications=[LongRange])
    # The Spinward Extents source rows apply the close-structure hull cost but
    # do not apply the HG close-structure armour volume modifier to armour tons.
    close_reinforced = hull.close_structure.model_copy(update={'reinforced': True, 'armour_volume_modifier': 1.0})
    fusion_plant = FusionPlantTL8(output=52_500, customisation=_size_reduction(3))

    return ship.Ship(
        ship_class='Acrux',
        ship_type='Heavy Cruiser',
        military=True,
        tl=11,
        displacement=50_000,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(
            configuration=close_reinforced,
            armour=armour.CrystalironArmour(protection=11),
            radiation_shielding=True,
        ),
        drives=DriveSection(m_drive=MDrive5(), j_drive=JDrive2()),
        power=PowerSection(plant=fusion_plant),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=8),
            fuel_processor=FuelProcessor(tons=250),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Core60(),
            backup_hardware=Core50(),
            software=[
                AutoRepair(rating=1),
                Evade(rating=2),
                AdvancedFireControl(rating=1),
                AntiHijack(rating=1),
                BattleSystem(rating=1),
                ElectronicWarfare(rating=1),
                LaunchSolution(rating=2),
                VirtualCrew(rating=0),
            ],
        ),
        sensors=SensorsSection(primary=MilitarySensors(), extended_arrays=ExtendedArrays()),
        weapons=WeaponsSection(
            spinal_mounts=[ParticleAcceleratorSpinalMount(size_multiple=2)],
            bays=[
                *[LargeMissileBay(customisation=_size_reduction(3)) for _ in range(5)],
                *[LargeTorpedoBay(customisation=_size_reduction(2)) for _ in range(5)],
                *[MediumParticleBeamBay() for _ in range(10)],
            ],
            barbettes=[
                *[ParticleBarbette() for _ in range(50)],
                *[PlasmaBarbette() for _ in range(40)],
            ],
            turrets=[
                *[
                    TripleTurret(
                        weapons=[
                            PulseLaser(customisation=pulse_long_range),
                            PulseLaser(customisation=pulse_long_range),
                            PulseLaser(customisation=pulse_long_range),
                        ]
                    )
                    for _ in range(120)
                ],
                *[TripleTurret(weapons=[BeamLaser(), BeamLaser(), BeamLaser()]) for _ in range(90)],
                *[TripleTurret(weapons=[Sandcaster(), Sandcaster(), Sandcaster()]) for _ in range(60)],
            ],
            point_defense_batteries=[LaserPointDefenseBattery1() for _ in range(10)],
            missile_storage=MissileStorage(count=28_800),
            torpedo_storage=TorpedoStorage(count=7_200),
            sandcaster_canister_storage=SandcasterCanisterStorage(count=4_800),
        ),
        craft=CraftSection(
            internal_housing=[
                InternalDockingSpace(craft=EmptyOccupant(docking_space=1080)),
                FullHangar(craft=EmptyOccupant(docking_space=360)),
            ]
        ),
        habitation=HabitationSection(
            staterooms=[*[Stateroom() for _ in range(337)], *[HighStateroom() for _ in range(9)]],
            low_berths=[LowBerth() for _ in range(20)],
            brigs=[Brig() for _ in range(4)],
            barracks=[Barracks(tons=300, occupants='150 troops')],
            common_area=CommonArea(tons=346),
        ),
        systems=SystemsSection(
            internal_systems=[
                *[Armoury() for _ in range(50)],
                *[BriefingRoom() for _ in range(4)],
                *[MedicalBay() for _ in range(6)],
                TrainingFacility(trainees=50),
                UNREPSystem(tons=25),
                *[Workshop() for _ in range(17)],
            ],
            drones=[RepairDrones()],
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=428.5, crane=CargoCrane(), display_label='Cargo Bay')]),
    )


@pytest.mark.approval
def test_acrux_heavy_cruiser(snapshot):
    snap = AnnotatedSnapshot(build_acrux_heavy_cruiser().build_spec().model_dump(mode='json'))
    snap.annotate('error', 'Requires TL12, ship is TL11 — command bridge not modelled as Ceres CommandBridge')
    snap.annotate('cost', 'Armour cost not yet traced to an HG rule; source purchase/row totals are inconsistent')
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

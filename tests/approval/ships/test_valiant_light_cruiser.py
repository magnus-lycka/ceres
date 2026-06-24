"""Approval snapshot for the Valiant-class Light Cruiser.

Source: High Guard (official publication).

Purpose:
- provide a large-scale military source snapshot with spinal mounts, screens,
  and complex sensor/weapon arrays
- exercise Core/100fib, bonded superdense armour, size-reduced drives,
  decreased-fuel J-drive, and full-scale crew manifest
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import ComputerSection, Core100
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, SpaceCraft
from ceres.make.ship.crew import (
    Administrator,
    Astrogator,
    Captain,
    Engineer,
    Gunner,
    Maintenance,
    Marine,
    Medic,
    Officer,
    Pilot,
    SensorOperator,
    ShipCrew,
)
from ceres.make.ship.drives import DecreasedFuel, DriveSection, FusionPlantTL15, JDrive4, MDrive5, PowerSection
from ceres.make.ship.habitation import HabitationSection, HighStateroom, Stateroom
from ceres.make.ship.parts import Advanced, HighTechnology, SizeReduction
from ceres.make.ship.screens import NuclearDamper, ScreensSection
from ceres.make.ship.sensors import (
    AdvancedSensors,
    EnhancedSignalProcessing,
    ExtendedArrays,
    MilitaryCountermeasuresSuite,
    SensorsSection,
)
from ceres.make.ship.software import (
    AdvancedFireControl,
    AntiHijack,
    BattleSystem,
    BroadSpectrumEW,
    ElectronicWarfare,
    LaunchSolution,
    PointDefence,
)
from ceres.make.ship.storage import (
    CargoHold,
    CargoSection,
    FuelProcessor,
    FuelScoops,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import (
    Armoury,
    BriefingRoom,
    CommandBridge,
    CommonArea,
    MedicalBay,
    SystemsSection,
    Workshop,
)
from ceres.make.ship.weapons import (
    BeamLaser,
    LaserPointDefenseBattery2,
    MediumRepulsorBay,
    MesonSpinalMount,
    MissileRack,
    MissileStorage,
    Sandcaster,
    SandcasterCanisterStorage,
    TripleTurret,
    WeaponsSection,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def _size_reduction(steps: int):
    if steps == 3:
        return HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction])
    raise ValueError(f'Valiant only uses size reduction x3, got x{steps}')


def _decreased_fuel():
    return Advanced(modifications=[DecreasedFuel])


def build_valiant_light_cruiser() -> ship.Ship:
    """Note: High Guard Valiant source snapshot is mostly modelled.

    Still missing for a complete Valiant: investigation of the beam laser
    turret source cost and a policy for the source's mutually inconsistent
    purchase/table/row totals.
    """
    reinforced_hull = hull.standard_hull.model_copy(update={'reinforced': True})
    modular_cutter = SpaceCraft.from_catalog('Modular Cutter')

    return ship.Ship(
        ship_class='Valiant',
        ship_type='Light Cruiser',
        military=True,
        tl=15,
        displacement=30_000,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(
            configuration=reinforced_hull,
            armour=armour.BondedSuperdenseArmour(protection=15),
            radiation_shielding=True,
        ),
        drives=DriveSection(
            m_drive=MDrive5(customisation=_size_reduction(3)), j_drive=JDrive4(customisation=_decreased_fuel())
        ),
        power=PowerSection(plant=FusionPlantTL15(output=24_000)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=4),
            operation_fuel=OperationFuel(weeks=8),
            fuel_scoops=FuelScoops(),
            fuel_processor=FuelProcessor(tons=50.0),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Core100(fib=True),
            software=[
                AdvancedFireControl(rating=2),
                AntiHijack(rating=3),
                BattleSystem(rating=2),
                BroadSpectrumEW(),
                ElectronicWarfare(rating=1),
                LaunchSolution(rating=3),
                PointDefence(rating=2),
            ],
        ),
        sensors=SensorsSection(
            primary=AdvancedSensors(),
            extended_arrays=ExtendedArrays(),
            signal_processing=EnhancedSignalProcessing(),
            countermeasures=MilitaryCountermeasuresSuite(),
        ),
        weapons=WeaponsSection(
            spinal_mounts=[MesonSpinalMount(tl_improvement=3)],
            bays=[MediumRepulsorBay()],
            turrets=[
                *[TripleTurret(weapons=[MissileRack(), MissileRack(), MissileRack()]) for _ in range(160)],
                *[TripleTurret(weapons=[BeamLaser(), BeamLaser(), BeamLaser()]) for _ in range(50)],
                *[TripleTurret(weapons=[Sandcaster(), Sandcaster(), Sandcaster()]) for _ in range(25)],
            ],
            point_defense_batteries=[LaserPointDefenseBattery2() for _ in range(4)],
            missile_storage=MissileStorage(count=9_600),
            sandcaster_canister_storage=SandcasterCanisterStorage(count=1_320),
        ),
        screens=ScreensSection(
            screens=[NuclearDamper(customisation=_size_reduction(3)) for _ in range(9)],
        ),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=modular_cutter) for _ in range(5)]),
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot() for _ in range(8)],
                Astrogator(),
                *[Engineer() for _ in range(101)],
                *[Maintenance() for _ in range(40)],
                *[Marine() for _ in range(20)],
                *[Medic() for _ in range(3)],
                *[Gunner() for _ in range(203)],
                *[Administrator() for _ in range(20)],
                *[Officer() for _ in range(40)],
                *[SensorOperator() for _ in range(8)],
            ]
        ),
        systems=SystemsSection(
            internal_systems=[
                *[CommandBridge()],
                *[Armoury() for _ in range(18)],
                *[BriefingRoom() for _ in range(2)],
                *[MedicalBay() for _ in range(4)],
                *[Workshop() for _ in range(2)],
            ]
        ),
        habitation=HabitationSection(
            staterooms=[HighStateroom(), *[Stateroom() for _ in range(265)]],
            common_area=CommonArea(tons=267.0),
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=317.0)]),
    )


@pytest.mark.approval
def test_valiant_light_cruiser(snapshot):
    snap = AnnotatedSnapshot(build_valiant_light_cruiser().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Triple Turrets (beam lasers) cost does not match current Ceres beam-laser turret model; '
        'source purchase cost, table total, and row total disagree with each other; '
        'source lists Jump Control/4 at zero cost but Ceres omits it (hardware-integrated in Core computers)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

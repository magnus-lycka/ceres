"""Approval snapshot for the Small Scout Base.

Source: refs/tycho/SmallScoutBase.txt.

Purpose:
- provide a large scout-base / space-station reference slice
- exercise light dispersed hulls, thrust-0 manoeuvre drives, full hangars,
  large explicit station crews, and large-scale habitation
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer20, ComputerSection
from ceres.make.ship.crafts import CraftSection, FullHangar, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import (
    Administrator,
    Engineer,
    GeneralCrew,
    Gunner,
    Maintenance,
    Medic,
    Officer,
    Pilot,
    SensorOperator,
    ShipCrew,
)
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive0, PowerSection
from ceres.make.ship.habitation import AdvancedEntertainmentSystem, Brig, HabitationSection, Stateroom
from ceres.make.ship.sensors import BasicSensors, SensorsSection
from ceres.make.ship.storage import FuelProcessor, FuelSection, OperationFuel
from ceres.make.ship.systems import (
    Airlock,
    Armoury,
    BriefingRoom,
    CommonArea,
    LibraryFacility,
    MedicalBay,
    MiningDrones,
    ProbeDrones,
    RepairDrones,
    SwimmingPool,
    SystemsSection,
    Theatre,
    TrainingFacility,
)
from ceres.make.ship.weapons import BeamLaser, MissileRack, QuadTurret, WeaponsSection
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_small_scout_base() -> ship.Ship:
    light_dispersed = hull.dispersed_structure.model_copy(
        update={'light': True, 'description': 'Light Dispersed Structure Hull'}
    )
    return ship.Ship(
        ship_class='Small Scout Base',
        tl=12,
        displacement=10_000,
        design_type=ship.ShipDesignType.STANDARD,
        occupants=[],
        crew=ShipCrew(
            roles=[
                *[Engineer()] * 6,
                *[GeneralCrew()] * 250,
                *[Maintenance()] * 9,
                *[Gunner()] * 5,
                *[Administrator()] * 4,
                SensorOperator(),
                *[Pilot()] * 13,
                *[Medic()] * 2,
                *[Officer()] * 14,
            ]
        ),
        hull=hull.Hull(configuration=light_dispersed, airlocks=[Airlock() for _ in range(24)]),
        drives=DriveSection(m_drive=MDrive0()),
        power=PowerSection(plant=FusionPlantTL12(output=2_500)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=5),
        ),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer20()),
        sensors=SensorsSection(primary=BasicSensors()),
        weapons=WeaponsSection(
            turrets=[
                *[
                    QuadTurret(
                        weapons=[BeamLaser()] * 4,
                    )
                ]
                * 4,
                QuadTurret(
                    weapons=[MissileRack()] * 4,
                ),
            ]
        ),
        craft=CraftSection(
            internal_housing=[
                *[FullHangar(craft=SpaceCraft.from_catalog('Passenger Shuttle'))] * 10,
                *[FullHangar(craft=SpaceCraft.from_catalog("Ship's Boat"))] * 2,
                *[InternalDockingSpace(craft=Vehicle.from_catalog('G/Carrier'))] * 3,
            ]
        ),
        systems=SystemsSection(
            internal_systems=[
                Armoury(),
                BriefingRoom(),
                LibraryFacility(),
                MedicalBay(),
                MedicalBay(),
                TrainingFacility(trainees=4),
            ],
            drones=[MiningDrones(count=10), ProbeDrones(count=100), RepairDrones()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 1_250,
            brig=Brig(),
            common_area=CommonArea(tons=1_250.0),
            entertainment=AdvancedEntertainmentSystem(cost=10_000),
            swimming_pool=SwimmingPool(tons=4.0),
            theatres=[Theatre(tons=8.0)],
        ),
    )


@pytest.mark.approval
def test_small_scout_base(snapshot):
    snap = AnnotatedSnapshot(build_small_scout_base().build_spec().model_dump(mode='json'))
    snap.annotate(
        'hull_points',
        'Ref sheet lists HULL: 3,200; Ceres gives 3,240 per light+dispersed modifiers',
    )
    snap.annotate(
        'fuel',
        'Ref shows 51t operation fuel (includes 1t from improved solar panel not modelled); Ceres gives 50t',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

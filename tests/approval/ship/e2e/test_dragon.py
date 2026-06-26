"""Approval snapshot for the Dragon System Defense Boat.

Source: refs/tycho/dragon.txt.

Purpose:
- preserve a source-derived military baseline for the Dragon line
- exercise reinforced streamlined TL13 SDB modelling with bulkheads, sensors,
  bays, barbettes, point defence, and military crew rules
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer20, Computer25, ComputerSection
from ceres.make.ship.crew import (
    Astrogator,
    Captain,
    Engineer,
    Gunner,
    Maintenance,
    Medic,
    Officer,
    Pilot,
    SensorOperator,
    ShipCrew,
)
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive7, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.hull import ImprovedStealth
from ceres.make.ship.parts import HighTechnology, SizeReduction
from ceres.make.ship.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ExtendedArrays,
    ImprovedSensors,
    SensorsSection,
    SensorStations,
)
from ceres.make.ship.software import (
    AutoRepair,
    Evade,
    FireControl,
)
from ceres.make.ship.storage import FuelSection, OperationFuel
from ceres.make.ship.systems import (
    Airlock,
    Armoury,
    Biosphere,
    CommonArea,
    MedicalBay,
    RepairDrones,
    SystemsSection,
    TrainingFacility,
    Workshop,
)
from ceres.make.ship.weapons import (
    LaserPointDefenseBattery2,
    MissileStorage,
    ParticleBarbette,
    SmallMissileBay,
    WeaponsSection,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_dragon() -> ship.Ship:
    """
    Build the Dragon reference case from refs/tycho/dragon.txt.

    Source aspects intentionally not carried over verbatim:
    - exact bay count/formatting from source export
    """

    return ship.Ship(
        ship_class='Dragon',
        ship_type='System Defense Boat',
        military=True,
        tl=13,
        displacement=400,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull.model_copy(
                update={'reinforced': True},
            ),
            stealth=ImprovedStealth(),
            radiation_shielding=True,
            armour=armour.CrystalironArmour(protection=13),
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive7(armoured_bulkhead=True)),
        power=PowerSection(plant=FusionPlantTL12(output=450, armoured_bulkhead=True)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=16, armoured_bulkhead=True)),
        command=CommandSection(bridge=Bridge(holographic=True, armoured_bulkhead=True)),
        computer=ComputerSection(
            hardware=Computer25(fib=True),
            backup_hardware=Computer20(fib=True),
            software=[AutoRepair(rating=1), FireControl(rating=2), Evade(rating=1)],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(armoured_bulkhead=True),
            countermeasures=CountermeasuresSuite(armoured_bulkhead=True),
            signal_processing=EnhancedSignalProcessing(armoured_bulkhead=True),
            extended_arrays=ExtendedArrays(armoured_bulkhead=True),
            sensor_stations=SensorStations(count=2, armoured_bulkhead=True),
        ),
        weapons=WeaponsSection(
            barbettes=[
                ParticleBarbette(armoured_bulkhead=True),
                ParticleBarbette(armoured_bulkhead=True),
            ],
            bays=[
                SmallMissileBay(
                    customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                )
            ],
            point_defense_batteries=[LaserPointDefenseBattery2(armoured_bulkhead=True)],
            missile_storage=MissileStorage(count=480, armoured_bulkhead=True),
        ),
        systems=SystemsSection(
            internal_systems=[
                Armoury(),
                Biosphere(tons=4.0),
                MedicalBay(),
                TrainingFacility(trainees=2),
                Workshop(),
            ],
            drones=[RepairDrones()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            common_area=CommonArea(tons=10.0),
        ),
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 3,
                Astrogator(),
                *[Engineer()] * 2,
                Maintenance(),
                Medic(),
                *[Gunner()] * 6,
                *[SensorOperator()] * 3,
                Officer(),
            ]
        ),
    )


@pytest.mark.approval
def test_dragon(snapshot):
    snap = AnnotatedSnapshot(build_dragon().build_spec().model_dump(mode='json'))
    snap.annotate(
        'life_support',
        'Ceres calculates 29,000 from stateroom occupancy; source shows 22,000 (source inconsistency)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

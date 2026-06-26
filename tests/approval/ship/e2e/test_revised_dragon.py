"""Approval snapshot for the Revised Dragon System Defense Boat.

Source: refs/tycho/revised_dragon.txt.

Purpose:
- preserve a source-derived revised military Dragon variant
- exercise customisations beyond the baseline Dragon, including budget drives,
  very-high-yield barbettes, energy-efficient point defence, and modest
  habitation upgrades
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer20, Computer25, ComputerSection
from ceres.make.ship.crew import (
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
from ceres.make.ship.habitation import AdvancedEntertainmentSystem, HabitationSection, Stateroom
from ceres.make.ship.hull import ImprovedStealth
from ceres.make.ship.parts import (
    Advanced,
    Budget,
    EnergyEfficient,
    HighTechnology,
    IncreasedSize,
    SizeReduction,
    VeryAdvanced,
)
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
    VeryHighYield,
    WeaponsSection,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_revised_dragon() -> ship.Ship:
    """Build the revised Dragon reference case from refs/tycho/revised_dragon.txt."""

    return ship.Ship(
        ship_class='Dragon',
        ship_type='System Defense Boat, Revised',
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
        drives=DriveSection(
            m_drive=MDrive7(customisation=Budget(modifications=[IncreasedSize]), armoured_bulkhead=True)
        ),
        power=PowerSection(
            plant=FusionPlantTL12(
                output=482,
                customisation=Budget(modifications=[IncreasedSize]),
                armoured_bulkhead=True,
            )
        ),
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
                ParticleBarbette(customisation=VeryAdvanced(modifications=[VeryHighYield]), armoured_bulkhead=True),
                ParticleBarbette(customisation=VeryAdvanced(modifications=[VeryHighYield]), armoured_bulkhead=True),
            ],
            bays=[
                SmallMissileBay(
                    customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                )
            ],
            point_defense_batteries=[
                LaserPointDefenseBattery2(
                    customisation=Advanced(modifications=[EnergyEfficient]),
                    armoured_bulkhead=True,
                )
            ],
            missile_storage=MissileStorage(count=408, armoured_bulkhead=True),
        ),
        systems=SystemsSection(
            internal_systems=[Armoury(), MedicalBay(), TrainingFacility(trainees=2), Workshop()],
            drones=[RepairDrones()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            common_area=CommonArea(tons=10.0),
            entertainment=AdvancedEntertainmentSystem(cost=500),
        ),
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 3,
                *[Engineer()] * 3,
                Maintenance(),
                Medic(),
                *[Gunner()] * 5,
                *[SensorOperator()] * 3,
                *[Officer()] * 2,
            ]
        ),
    )


@pytest.mark.approval
def test_revised_dragon(snapshot):
    snap = AnnotatedSnapshot(build_revised_dragon().build_spec().model_dump(mode='json'))
    snap.annotate(
        'fuel',
        'Operation fuel: Ceres rounds up to 17t; ref shows 16.07t',
    )
    snap.annotate(
        'cargo',
        'Ceres gives 4.31t vs ref ~5.24t (fuel tons rounding + RIS-001 stores not modelled separately)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

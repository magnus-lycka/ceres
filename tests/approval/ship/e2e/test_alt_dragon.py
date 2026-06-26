"""Approval snapshot for the alternate Dragon reference case.

Source: refs/tycho/alt_dragon.txt.

Purpose:
- preserve a source-derived alternate military Dragon variant
- exercise additional optional systems such as emergency power, rapid
  deployment arrays, biosphere support, autodoc, cabin space, and upgraded
  computing
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer20, ComputerSection, Core40
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
from ceres.make.ship.drives import (
    DriveSection,
    EmergencyPowerSystem,
    FusionPlantTL12,
    MDrive7,
    PowerSection,
)
from ceres.make.ship.habitation import AdvancedEntertainmentSystem, CabinSpace, HabitationSection, Stateroom
from ceres.make.ship.hull import ImprovedStealth
from ceres.make.ship.parts import Advanced, Budget, HighTechnology, IncreasedSize, SizeReduction
from ceres.make.ship.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ImprovedSensors,
    RapidDeploymentExtendedArrays,
    SensorsSection,
)
from ceres.make.ship.software import (
    AutoRepair,
    Evade,
    FireControl,
)
from ceres.make.ship.storage import FuelProcessor, FuelSection, OperationFuel
from ceres.make.ship.systems import (
    Airlock,
    Armoury,
    BasicAutodoc,
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


def build_alt_dragon() -> ship.Ship:
    """Build the alternate Dragon reference case from refs/tycho/alt_dragon.txt."""

    fusion_plant = FusionPlantTL12(
        output=436, customisation=Advanced(modifications=[SizeReduction]), armoured_bulkhead=True
    )

    return ship.Ship(
        ship_class='Dragon',
        ship_type='System Defense Boat, Alternate',
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
            armoured_bulkheads=[],
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(
            m_drive=MDrive7(customisation=Budget(modifications=[IncreasedSize]), armoured_bulkhead=True)
        ),
        power=PowerSection(
            plant=fusion_plant,
            emergency_power_system=EmergencyPowerSystem.from_fusion_plant(fusion_plant),
        ),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=16, armoured_bulkhead=True),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge(holographic=True, armoured_bulkhead=True)),
        computer=ComputerSection(
            hardware=Core40(fib=True, retro_levels=2),
            backup_hardware=Computer20(fib=True, retro_levels=1),
            software=[AutoRepair(rating=1), FireControl(rating=2), Evade(rating=1)],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(),
            countermeasures=CountermeasuresSuite(),
            signal_processing=EnhancedSignalProcessing(),
            extended_arrays=RapidDeploymentExtendedArrays(),
        ),
        weapons=WeaponsSection(
            barbettes=[
                ParticleBarbette(customisation=Advanced(modifications=[SizeReduction]), armoured_bulkhead=True),
                ParticleBarbette(customisation=Advanced(modifications=[SizeReduction]), armoured_bulkhead=True),
            ],
            bays=[
                SmallMissileBay(
                    customisation=HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                )
            ],
            point_defense_batteries=[
                LaserPointDefenseBattery2(customisation=Advanced(modifications=[SizeReduction]), armoured_bulkhead=True)
            ],
            missile_storage=MissileStorage(count=720, armoured_bulkhead=True),
        ),
        systems=SystemsSection(
            internal_systems=[
                Armoury(),
                Biosphere(tons=4.0),
                MedicalBay(autodoc=BasicAutodoc()),
                TrainingFacility(trainees=2),
                Workshop(),
            ],
            drones=[RepairDrones()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 4,
            cabin_space=CabinSpace(tons=15.0),
            common_area=CommonArea(tons=10.0),
            entertainment=AdvancedEntertainmentSystem(cost=1_250),
        ),
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 3,
                *[Engineer()] * 2,
                Maintenance(),
                Medic(),
                *[Gunner()] * 5,
                *[SensorOperator()] * 3,
                Officer(),
            ]
        ),
    )


@pytest.mark.approval
def test_alt_dragon(snapshot):
    snap = AnnotatedSnapshot(build_alt_dragon().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Computer cost uses retro_levels=2 (÷4) per RIS-005 instead of source retro_levels=4 (÷16); '
        'production and sales price higher than ref accordingly',
    )
    snap.annotate('fuel', 'Operation fuel rounds up to 11t; ref shows 10.46t (RIS-007)')
    snap.annotate('cargo', 'Ceres gives 5.8616t vs ref ~6.30t (fuel rounding + RIS-001 stores)')
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

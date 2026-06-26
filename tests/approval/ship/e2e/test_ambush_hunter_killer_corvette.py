"""Approval snapshot for the Ambush-class Hunter-Killer Corvette.

Source: refs/tycho/ambush_corvette (stat block screenshot).
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.armour import BondedSuperdenseArmour
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer30, ComputerSection
from ceres.make.ship.drives import (
    DecreasedFuel,
    DriveSection,
    FusionPlantTL12,
    JDrive2,
    MDrive6,
    PowerSection,
)
from ceres.make.ship.habitation import HabitationSection, HighStateroom, Stateroom
from ceres.make.ship.parts import EnergyEfficient, HighTechnology, SizeReduction, VeryAdvanced
from ceres.make.ship.sensors import (
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ImprovedSensors,
    SensorsSection,
    SensorStations,
)
from ceres.make.ship.software import (
    AdvancedFireControl,
    AntiHijack,
    BroadSpectrumEW,
    ElectronicWarfare,
    JumpControl,
    VirtualGunner,
)
from ceres.make.ship.storage import FuelProcessor, FuelSection, OperationFuel
from ceres.make.ship.systems import Airlock, Armoury, BriefingRoom, CommonArea, MedicalBay, RepairDrones, SystemsSection
from ceres.make.ship.weapons import (
    HighYield,
    LongRange,
    MediumParticleBeamBay,
    PulseLaser,
    TripleTurret,
    WeaponsSection,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_ambush_hunter_killer_corvette() -> ship.Ship:
    """
    Modeled subset of the Ambush-class Hunter-Killer Corvette reference.

    Not yet modeled from the reference:
    - reinforced hull as its own separate cost row
    - the exact reference crew panel
    """

    return ship.Ship(
        ship_class='Ambush-Class',
        ship_type='Hunter-Killer Corvette',
        military=True,
        tl=15,
        displacement=450,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(
            configuration=hull.close_structure.model_copy(
                update={'reinforced': True, 'description': 'Close Structure Hull, Reinforced'},
            ),
            armour=BondedSuperdenseArmour(protection=12),
            airlocks=[Airlock(), Airlock(), Airlock(), Airlock(), Airlock(), Airlock()],
        ),
        drives=DriveSection(
            m_drive=MDrive6(customisation=VeryAdvanced(modifications=[SizeReduction, EnergyEfficient])),
            j_drive=JDrive2(customisation=VeryAdvanced(modifications=[DecreasedFuel, DecreasedFuel])),
        ),
        power=PowerSection(plant=FusionPlantTL12(output=500, armoured_bulkhead=True)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=16),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(
            hardware=Computer30(),
            software=[
                JumpControl(rating=2),
                AdvancedFireControl(rating=1),
                AntiHijack(rating=1),
                BroadSpectrumEW(),
                ElectronicWarfare(rating=1),
                VirtualGunner(rating=1),
            ],
        ),
        sensors=SensorsSection(
            primary=ImprovedSensors(),
            countermeasures=CountermeasuresSuite(),
            signal_processing=EnhancedSignalProcessing(),
            sensor_stations=SensorStations(count=2),
        ),
        weapons=WeaponsSection(
            bays=[
                MediumParticleBeamBay(
                    customisation=HighTechnology(modifications=[HighYield, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                ),
                MediumParticleBeamBay(
                    customisation=HighTechnology(modifications=[HighYield, SizeReduction, SizeReduction]),
                    armoured_bulkhead=True,
                ),
            ],
            turrets=[
                TripleTurret(
                    weapons=[
                        PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield])),
                        PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield])),
                        PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield])),
                    ],
                ),
                TripleTurret(
                    weapons=[
                        PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield])),
                        PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield])),
                        PulseLaser(customisation=HighTechnology(modifications=[LongRange, HighYield])),
                    ],
                ),
            ],
        ),
        systems=SystemsSection(
            drones=[RepairDrones()],
            internal_systems=[Armoury(), BriefingRoom(), MedicalBay()],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 8 + [HighStateroom()],
            common_area=CommonArea(tons=12),
        ),
    )


@pytest.mark.approval
def test_ambush_hunter_killer_corvette(snapshot):
    snap = AnnotatedSnapshot(build_ambush_hunter_killer_corvette().build_spec().model_dump(mode='json'))
    snap.annotate('fuel', 'Op fuel Ceres gives 14t; stat block shows 16t (RIS-007)')
    snap.annotate(
        'cost',
        'Sales price = production (CUSTOM design, no discount); stat block shows discounted sales price. '
        'Maintenance based on full production cost.',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

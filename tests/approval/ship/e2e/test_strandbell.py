"""Approval snapshot for the Strandbell System Defense Boat.

Source: refs/tycho/sdb.md (Tycho design tool output for a 200-ton TL-15 SDB).

Purpose:
- exercise a 200-ton military standard reinforced hull with Crystaliron armour
- confirm M-Drive 9, Fusion TL12 power plant, and sensor suite behaviour
- validate turret costs and power, missile storage, and crew composition
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer35, ComputerSection
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive9, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import CountermeasuresSuite, ImprovedSensors, SensorsSection
from ceres.make.ship.software import (
    AutoRepair,
    Evade,
    FireControl,
)
from ceres.make.ship.storage import FuelProcessor, FuelScoops, FuelSection, OperationFuel
from ceres.make.ship.systems import Airlock, CommonArea, MedicalBay, RepairDrones, SystemsSection
from ceres.make.ship.weapons import BeamLaser, MissileRack, MissileStorage, TripleTurret, WeaponsSection
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot

STRANDBELL_HULL = hull.standard_hull.model_copy(
    update={'reinforced': True, 'description': 'Standard Reinforced Hull'},
)


def build_strandbell() -> ship.Ship:
    return ship.Ship(
        ship_class='Strandbell',
        ship_type='System Defense Boat',
        military=True,
        tl=15,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=STRANDBELL_HULL,
            armour=armour.CrystalironArmour(protection=13),
            airlocks=[Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive9()),
        power=PowerSection(plant=FusionPlantTL12(output=240)),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=1),
            fuel_scoops=FuelScoops(),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(
            hardware=Computer35(), software=[AutoRepair(rating=1), FireControl(rating=2), Evade(rating=2)]
        ),
        sensors=SensorsSection(primary=ImprovedSensors(), countermeasures=CountermeasuresSuite()),
        weapons=WeaponsSection(
            turrets=[
                TripleTurret(
                    weapons=[
                        BeamLaser(),
                        BeamLaser(),
                        BeamLaser(),
                    ],
                ),
                TripleTurret(
                    weapons=[
                        MissileRack(),
                        MissileRack(),
                        MissileRack(),
                    ],
                ),
            ],
            missile_storage=MissileStorage(count=240),
        ),
        systems=SystemsSection(internal_systems=[MedicalBay()], drones=[RepairDrones()]),
        habitation=HabitationSection(staterooms=[Stateroom()] * 15, common_area=CommonArea(tons=4.0)),
    )


@pytest.mark.approval
def test_strandbell(snapshot):
    snap = AnnotatedSnapshot(build_strandbell().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ref MCr147.13 includes armored bulkheads (MCr0.62) and stores/spares; Ceres gives MCr140.9 '
        '(armored M-drive bulkheads and stores not modelled)',
    )
    snap.annotate(
        'fuel',
        'Ceres gives op_fuel=5.0t per RIS-007; ref shows 4.80t for 12 weeks',
    )
    snap.annotate(
        'cargo',
        'Ceres gives 20.5t; ref shows 13.8t — armored M-drive bulkheads and stores/spares not modelled',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

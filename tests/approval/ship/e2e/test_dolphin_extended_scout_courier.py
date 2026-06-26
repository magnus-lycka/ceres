"""Approval snapshot for the Dolphin Class Extended Scout Courier.

Source: User-supplied Dolphin Class screenshot.

Purpose:
- provide a compact TL15 scout/courier reference variant
- exercise a slightly larger scout with triple turret, medical bay, and cargo
  fittings beyond the current Suleiman baseline
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer10, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.make.ship.crew import Astrogator, Engineer, Gunner, Medic, Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL15, JDrive2, MDrive2, PowerSection
from ceres.make.ship.habitation import HabitationSection, LowBerth, Stateroom
from ceres.make.ship.sensors import MilitarySensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import (
    CargoAirlock,
    CargoSection,
    FuelCargoContainer,
    FuelProcessor,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import CommonArea, MedicalBay, ProbeDrones, SystemsSection, Workshop
from ceres.make.ship.weapons import PulseLaser, TripleTurret, WeaponsSection
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_dolphin_extended_scout_courier() -> ship.Ship:
    return ship.Ship(
        ship_class='Dolphin Class',
        ship_type='Extended Scout Courier',
        tl=15,
        displacement=150,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull,
            armour=armour.CrystalironArmour(protection=4),
        ),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL15(output=70)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=16),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer10(), software=[JumpControl(rating=2)]),
        sensors=SensorsSection(primary=MilitarySensors()),
        weapons=WeaponsSection(
            turrets=[
                TripleTurret(
                    weapons=[
                        PulseLaser(),
                        PulseLaser(),
                        PulseLaser(),
                    ],
                )
            ]
        ),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))]),
        systems=SystemsSection(
            internal_systems=[MedicalBay(), Workshop()],
            drones=[ProbeDrones(count=10)],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 4,
            common_area=CommonArea(tons=4.0),
            low_berths=[LowBerth()] * 4,
        ),
        cargo=CargoSection(
            cargo_airlocks=[CargoAirlock()],
            fuel_cargo_containers=[FuelCargoContainer(capacity=30)],
        ),
        crew=ShipCrew(roles=[Pilot(), Astrogator(), Engineer(), Gunner(), Medic()]),
    )


@pytest.mark.approval
def test_dolphin_extended_scout_courier(snapshot):
    snap = AnnotatedSnapshot(build_dolphin_extended_scout_courier().build_spec().model_dump(mode='json'))
    snap.annotate(
        'fuel',
        'Ceres rounds op fuel up to 2t for 150-ton ship (RIS-007), giving ~20 weeks endurance; '
        'source lists 16 weeks as 4t',
    )
    snap.annotate(
        'endurance',
        'Maintenance: Ceres gives 4534 vs stat block 4535 (off by Cr1 due to rounding difference)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

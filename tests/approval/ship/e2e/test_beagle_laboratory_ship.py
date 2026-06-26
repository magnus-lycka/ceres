"""Approval snapshot for the Beagle-class Laboratory Ship.

Source: refs/tycho/BeagleLaboratoryShip.txt.

Purpose:
- provide a laboratory-ship reference case that extends the lab-station cases
  with jump drive, weapons, biosphere, hot tubs, and mixed internal/external
  carried-craft fittings
"""

import pytest

from ceres.character.domain.skills import Level, SpaceScience
from ceres.gear.software import Expert
from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer10, ComputerSection
from ceres.make.ship.crafts import CraftSection, DockingClamp, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive2, PowerSection
from ceres.make.ship.habitation import HabitationSection, HotTub, LowBerth, Stateroom
from ceres.make.ship.sensors import ImprovedSensors, SensorsSection, SensorStations
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
from ceres.make.ship.systems import (
    AdvancedProbeDrones,
    Airlock,
    Biosphere,
    CommonArea,
    Laboratory,
    LibraryFacility,
    MedicalBay,
    SystemsSection,
    WetBar,
    Workshop,
)
from ceres.make.ship.weapons import (
    BeamLaser,
    DoubleTurret,
    MissileRack,
    MissileStorage,
    Sandcaster,
    SandcasterCanisterStorage,
    WeaponsSection,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_beagle_laboratory_ship() -> ship.Ship:
    return ship.Ship(
        ship_class='Beagle-class',
        ship_type='Laboratory Ship',
        tl=15,
        displacement=360,
        design_type=ship.ShipDesignType.STANDARD,
        occupants=[],
        hull=hull.Hull(
            configuration=hull.dispersed_structure,
            airlocks=[Airlock() for _ in range(3)],
        ),
        drives=DriveSection(m_drive=MDrive2(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=180)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=8),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge(small=True, holographic=True)),
        computer=ComputerSection(
            hardware=Computer10(),
            software=[JumpControl(rating=2), Expert(rating=3, skill=SpaceScience(planetology=Level(value=3)))],
        ),
        sensors=SensorsSection(primary=ImprovedSensors(), sensor_stations=SensorStations(count=1)),
        weapons=WeaponsSection(
            turrets=[
                DoubleTurret(weapons=[BeamLaser(), BeamLaser()]),
                DoubleTurret(weapons=[MissileRack(), Sandcaster()]),
            ],
            missile_storage=MissileStorage(count=12),
            sandcaster_canister_storage=SandcasterCanisterStorage(count=20),
        ),
        craft=CraftSection(
            docking_clamps=[
                DockingClamp(craft=SpaceCraft.from_catalog('Pinnace'), transported=True, maintained=True),
                DockingClamp(craft=Vehicle.from_catalog('ATV'), transported=False, maintained=False),
            ],
            internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))],
        ),
        systems=SystemsSection(
            drones=[AdvancedProbeDrones(count=10)],
            internal_systems=[
                Biosphere(tons=2.0),
                *[Laboratory()] * 10,
                LibraryFacility(),
                MedicalBay(),
                Workshop(),
            ],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            common_area=CommonArea(tons=10.0),
            hot_tubs=[HotTub(users=1)] * 4,
            wet_bar=WetBar(),
            low_berths=[LowBerth()] * 6,
        ),
        cargo=CargoSection(
            cargo_airlocks=[CargoAirlock(size=4.0)],
            fuel_cargo_containers=[FuelCargoContainer(capacity=80)],
        ),
        crew=ShipCrew(),
    )


@pytest.mark.approval
def test_beagle_laboratory_ship(snapshot):
    snap = AnnotatedSnapshot(build_beagle_laboratory_ship().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        "Ceres uses 360t hull (MCr9 vs ref MCr10); no Ship's Mechanic (-MCr0.05); adds Expert software (+MCr0.02); "
        'production and sales price differ from ref accordingly',
    )
    snap.annotate(
        'cargo_airlock',
        'Ceres cargo airlock size=4 → 4 tons, MCr0.4; ref shows 2 tons, MCr0.2',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

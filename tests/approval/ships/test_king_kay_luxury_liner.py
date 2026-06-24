"""Approval snapshot for the King Kay Luxury Liner.

Source: refs/tycho/KingKayLuxuryLiner.csv.

Purpose:
- provide a large source-derived commercial liner reference slice
- exercise close-structure hulls, large TL12 jump/fusion hardware, holographic
  bridge controls, luxury/high/standard accommodation, and large docking spaces
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, Computer10, ComputerSection
from ceres.make.ship.crafts import CraftSection, EmptyOccupant, InternalDockingSpace
from ceres.make.ship.crew import (
    Administrator,
    Astrogator,
    Captain,
    Engineer,
    GeneralCrew,
    Maintenance,
    Marine,
    Medic,
    Officer,
    Pilot,
    ShipCrew,
    Steward,
)
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive1, PowerSection
from ceres.make.ship.habitation import HabitationSection, HighStateroom, LowBerth, LuxuryStateroom, Stateroom
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import FuelSection, JumpFuel, OperationFuel
from ceres.make.ship.systems import (
    CommercialZone,
    CommonArea,
    MedicalBay,
    SwimmingPool,
    SystemsSection,
    Theatre,
    WetBar,
)
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_king_kay() -> ship.Ship:
    """Build the modeled King Kay reference slice from refs/KingKayLuxuryLiner.csv."""
    return ship.Ship(
        ship_class='King Kay',
        ship_type='Luxury Liner',
        tl=12,
        displacement=5_000,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(configuration=hull.close_structure),
        drives=DriveSection(m_drive=MDrive1(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=2_010)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=8),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(
            hardware=Computer10(),
            backup_hardware=Computer5(bis=True),
            software=[JumpControl(rating=2)],
        ),
        sensors=SensorsSection(primary=CivilianSensors()),
        craft=CraftSection(
            internal_housing=[
                InternalDockingSpace(craft=EmptyOccupant(docking_space=70)),
                InternalDockingSpace(craft=EmptyOccupant(docking_space=70)),
                InternalDockingSpace(craft=EmptyOccupant(docking_space=252)),
            ]
        ),
        systems=SystemsSection(
            internal_systems=[MedicalBay(), CommercialZone(tons=240)],
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 80 + [HighStateroom()] * 192 + [LuxuryStateroom()] * 8,
            common_area=CommonArea(tons=388),
            swimming_pool=SwimmingPool(tons=60),
            theatres=[Theatre(tons=100), Theatre(tons=100), Theatre(tons=100)],
            wet_bar=WetBar(),
            low_berths=[LowBerth()] * 18,
        ),
        crew=ShipCrew(
            roles=[
                Captain(),
                *[Pilot()] * 3,
                Astrogator(),
                *[Engineer()] * 16,
                *[GeneralCrew()] * 55,
                *[Maintenance()] * 5,
                *[Steward()] * 65,
                *[Administrator()] * 10,
                *[Medic()] * 5,
                *[Officer()] * 11,
                *[Marine()] * 10,
            ]
        ),
    )


@pytest.mark.approval
def test_king_kay_luxury_liner(snapshot):
    snap = AnnotatedSnapshot(build_king_kay().build_spec().model_dump(mode='json'))
    snap.annotate(
        'fuel',
        'Ref shows J-2 + 8 weeks combined 1028t; Ceres: 1000 + 27 = 1027t (1t gap in op fuel calculation)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

"""Approval snapshot for the Revised Beowulf Free Trader.

Source: refs/tycho/RevisedBowulf.md.

Purpose:
- exercise a lighter revised Beowulf variant against the same baseline rules
  as the standard Beowulf
"""

import pytest

from ceres.make.ship import armour, hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crew import Astrogator, Engineer, Pilot, ShipCrew, Steward
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive1, MDrive1, PowerSection
from ceres.make.ship.habitation import AdvancedEntertainmentSystem, HabitationSection, LowBerth, Stateroom
from ceres.make.ship.occupants import MiddlePassage
from ceres.make.ship.parts import Budget, IncreasedSize
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import (
    CargoCrane,
    CargoHold,
    CargoSection,
    FuelProcessor,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import Airlock, CommonArea, MedicalBay, SystemsSection, Workshop
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_revised_beowulf() -> ship.Ship:
    """
    Build the Revised Beowulf reference case from refs/tycho/RevisedBowulf.md.

    Excluded from this reference mapping:
    - cost reduction on M-drive and jump drive
    - advanced low berth pricing/details
    - the reference expense assumptions for life support and purchased fuel
    """

    return ship.Ship(
        ship_class='Beowulf',
        ship_type='Free Trader, Revised',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=hull.streamlined_hull.model_copy(
                update={'light': True, 'description': 'Light Streamlined Hull'},
            ),
            armour=armour.CrystalironArmour(protection=2),
            airlocks=[Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive1(), j_drive=JDrive1()),
        power=PowerSection(plant=FusionPlantTL12(output=65, customisation=Budget(modifications=[IncreasedSize]))),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=1),
            operation_fuel=OperationFuel(weeks=4),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(hardware=Computer5(), software=[JumpControl(rating=1)]),
        sensors=SensorsSection(primary=CivilianSensors()),
        systems=SystemsSection(internal_systems=[MedicalBay(), Workshop()]),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 10,
            low_berths=[LowBerth()] * 20,
            common_area=CommonArea(tons=10.0),
            entertainment=AdvancedEntertainmentSystem(cost=5_000),
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=67.5, crane=CargoCrane(), display_label='Cargo Bay')]),
        crew=ShipCrew(roles=[Pilot(), Astrogator(), Engineer(), Steward()]),
        occupants=[MiddlePassage()] * 16,
    )


@pytest.mark.approval
def test_revised_beowulf(snapshot):
    snap = AnnotatedSnapshot(build_revised_beowulf().build_spec().model_dump(mode='json'))
    snap.annotate(
        'cost',
        'Ceres does not model cost-reduction drives; m_drive MCr4.0 vs ref MCr3.2, j_drive MCr15.0 vs ref MCr10.5; '
        'production cost MCr49.785 vs ref MCr46.285; maintenance MCr3734 vs ref MCr3471',
    )
    snap.annotate('fuel', 'Ceres gives op_fuel=1.0t per RIS-007 (1-ton minimum); ref shows 0.54t')
    snap.annotate(
        'life_support',
        'Ceres gives 30,000 (4 crew + 16 middle pax); ref shows 31,000 (source inconsistency)',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

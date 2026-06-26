"""Approval snapshot for the Pinnace with 20 ton fuel capacity.

Source: refs/tycho/PinnaceWith20TonFuelCapacity.txt.

Purpose:
- provide a compact small-craft reference case with a large fuel/cargo
  container and explicit purchased airlock
"""

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crew import Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, MDrive5, PowerSection
from ceres.make.ship.habitation import CabinSpace, HabitationSection
from ceres.make.ship.sensors import BasicSensors, SensorsSection
from ceres.make.ship.storage import CargoSection, FuelCargoContainer, FuelSection, OperationFuel
from ceres.make.ship.systems import Airlock, SystemsSection
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def build_pinnace_with_20_ton_fuel_capacity() -> ship.Ship:
    return ship.Ship(
        ship_class='Pinnace',
        ship_type='with 20 ton fuel capacity',
        tl=12,
        displacement=40,
        design_type=ship.ShipDesignType.STANDARD,
        occupants=[],
        crew=ShipCrew(roles=[Pilot()]),
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
        drives=DriveSection(m_drive=MDrive5()),
        power=PowerSection(plant=FusionPlantTL12(output=30)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=4)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        sensors=SensorsSection(primary=BasicSensors()),
        systems=SystemsSection(),
        habitation=HabitationSection(cabin_space=CabinSpace(tons=9)),
        cargo=CargoSection(fuel_cargo_containers=[FuelCargoContainer(capacity=20)]),
    )


@pytest.mark.approval
def test_pinnace_with_20_ton_fuel_capacity(snapshot):
    snap = AnnotatedSnapshot(build_pinnace_with_20_ton_fuel_capacity().build_spec().model_dump(mode='json'))
    snap.annotate(
        'fuel',
        'Ceres gives op_fuel=0.2t per RIS-007 (small craft rounding); ref shows 1t',
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

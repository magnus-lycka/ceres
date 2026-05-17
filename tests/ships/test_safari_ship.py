"""Reference ship case based on refs/hg/66_prospecting_buggy.md, page 173.

Purpose:
- provide a compact High Guard source snapshot with a named common-area space
- exercise generic part display labels on a real ship/gallery entry
- keep the source's distinction between ordinary common area and a labelled
  trophy lounge without introducing a dedicated TrophyLounge rule class

Source handling for this test case:
- supported: hull, drives, power plant, fuel tankage, bridge, computer,
  civilian sensors, empty double turret, docking spaces, carried launch and
  air/raft, fuel scoops, fuel processor, staterooms, common area, trophy
  lounge, cargo, software, and explicit crew manifest
- still excluded from the modeled reference case:
  - multi-environment equipment
  - multi-environment holding tanks
  - ATV carried on the launch
  - total cost, purchase cost, maintenance cost, and crew/life-support totals
"""

from types import SimpleNamespace

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crafts import CraftSection, InternalDockingSpace, SpaceCraft, Vehicle
from ceres.make.ship.crew import Astrogator, Engineer, Medic, Pilot, ShipCrew, Steward
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive2, MDrive1, PowerSection
from ceres.make.ship.habitation import HabitationSection, Stateroom
from ceres.make.ship.sensors import CivilianSensors, SensorsSection
from ceres.make.ship.software import JumpControl
from ceres.make.ship.storage import (
    CargoHold,
    CargoSection,
    FuelProcessor,
    FuelScoops,
    FuelSection,
    JumpFuel,
    OperationFuel,
)
from ceres.make.ship.systems import CommonArea
from ceres.make.ship.weapons import DoubleTurret, WeaponsSection

_expected = SimpleNamespace(
    ship_class='Type-K',
    ship_type='Safari Ship',
    tl=12,
    displacement=200,
    common_area_tons=13.0,
    common_area_cost_mcr=1.3,
    trophy_lounge_tons=7.0,
    trophy_lounge_cost_mcr=0.7,
    expected_errors=[],
    expected_warnings=[],
)


def build_safari_ship() -> ship.Ship:
    """Note: Incomplete Type-K Safari Ship slice; multi-environment systems and launch-carried ATV remain unmodeled."""
    return ship.Ship(
        ship_class='Type-K',
        ship_type='Safari Ship',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(m_drive=MDrive1(), j_drive=JDrive2()),
        power=PowerSection(plant=FusionPlantTL12(output=105)),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=2),
            operation_fuel=OperationFuel(weeks=4),
            fuel_scoops=FuelScoops(free=True),
            fuel_processor=FuelProcessor(tons=2),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(bis=True), software=[JumpControl(rating=2)]),
        sensors=SensorsSection(primary=CivilianSensors()),
        weapons=WeaponsSection(turrets=[DoubleTurret()]),
        craft=CraftSection(
            internal_housing=[
                InternalDockingSpace(craft=SpaceCraft.from_catalog('Launch')),
                InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft')),
            ]
        ),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 11,
            common_area=CommonArea(tons=13),
            common_areas=[CommonArea(tons=7, display_label='Trophy Lounge')],
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=13.2)]),
        crew=ShipCrew(roles=[Pilot(), Astrogator(), Engineer(), Steward(), Medic()]),
    )


@pytest.fixture(scope='module')
def safari_ship():
    return build_safari_ship()


@pytest.fixture(scope='module')
def safari_ship_spec(safari_ship):
    return safari_ship.build_spec()


def test_safari_ship_named_common_area_matches_reference_slice(safari_ship):
    assert safari_ship.ship_class == _expected.ship_class
    assert safari_ship.ship_type == _expected.ship_type
    assert safari_ship.tl == _expected.tl
    assert safari_ship.displacement == _expected.displacement
    assert safari_ship.habitation is not None
    assert safari_ship.habitation.common_area is not None
    assert safari_ship.habitation.common_area.tons == pytest.approx(_expected.common_area_tons)
    assert safari_ship.habitation.common_area.cost == pytest.approx(_expected.common_area_cost_mcr * 1_000_000)
    assert [area.tons for area in safari_ship.habitation.common_areas] == pytest.approx(
        [_expected.trophy_lounge_tons]
    )
    assert [area.cost for area in safari_ship.habitation.common_areas] == pytest.approx(
        [_expected.trophy_lounge_cost_mcr * 1_000_000]
    )
    assert safari_ship.notes.errors == _expected.expected_errors
    assert safari_ship.notes.warnings == _expected.expected_warnings


def test_safari_ship_spec_shows_trophy_lounge_display_label(safari_ship_spec):
    common_area = safari_ship_spec.row('Common Area', section='Habitation')
    assert common_area.tons == pytest.approx(_expected.common_area_tons)

    trophy_lounge = safari_ship_spec.row('Trophy Lounge (Common Area)', section='Habitation')
    assert trophy_lounge.tons == pytest.approx(_expected.trophy_lounge_tons)
    assert trophy_lounge.cost == pytest.approx(_expected.trophy_lounge_cost_mcr * 1_000_000)

import pytest

from ceres.build.ship import hull, ship
from ceres.build.ship.bridge import Bridge, CommandSection
from ceres.build.ship.computer import Computer, ComputerSection
from ceres.build.ship.drives import DriveSection, FusionPlantTL8, MDrive, PowerSection
from ceres.build.ship.habitation import HabitationSection, Stateroom
from ceres.build.ship.sensors import BasicSensors, SensorsSection
from ceres.build.ship.storage import CargoSection, FuelSection, OperationFuel
from ceres.build.ship.systems import Airlock, CommonArea, SystemsSection, Workshop


BOXY_HULL = hull.close_structure.model_copy(
    update={'light': True, 'description': 'Light Close Structure Hull'},
)


def build_boxy_ore_freighter() -> ship.Ship:
    return ship.Ship(
        ship_class='Boxy',
        ship_type='Ore Freighter',
        tl=9,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(configuration=BOXY_HULL, airlocks=[Airlock()]),
        drives=DriveSection(m_drive=MDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL8(output=80)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=12)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer(5)),
        sensors=SensorsSection(primary=BasicSensors()),
        habitation=HabitationSection(staterooms=[Stateroom()], common_area=CommonArea(tons=1.0)),
        systems=SystemsSection(internal_systems=[Workshop()]),
    )



def test_boxy_ore_freighter_has_large_default_cargo_hold():
    freighter = build_boxy_ore_freighter()
    assert CargoSection.cargo_tons_for_ship(freighter) == pytest.approx(170.0)


def test_boxy_ore_freighter_tl9_mdrive_is_valid():
    freighter = build_boxy_ore_freighter()
    assert freighter.drives is not None
    assert freighter.drives.m_drive is not None
    assert ('error', 'Requires TL10, ship is TL8') not in [
        (note.category.value, note.message) for note in freighter.drives.m_drive.notes
    ]


def test_boxy_ore_freighter_operation_fuel_costs_80_per_month():
    freighter = build_boxy_ore_freighter()
    assert freighter.expenses.fuel == pytest.approx(100.0)

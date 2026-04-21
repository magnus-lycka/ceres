import pytest

from tycho import hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection
from tycho.drives import DriveSection, FusionPlantTL8, MDrive, PowerSection
from tycho.habitation import HabitationSection, Staterooms
from tycho.sensors import BasicSensors, SensorsSection
from tycho.storage import CargoSection, FuelSection, OperationFuel
from tycho.systems import Airlock, CommonArea, SystemsSection, Workshop


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
        habitation=HabitationSection(staterooms=Staterooms(count=1), common_area=CommonArea(tons=1.0)),
        systems=SystemsSection(workshop=Workshop()),
    )



def test_boxy_ore_freighter_has_large_default_cargo_hold():
    freighter = build_boxy_ore_freighter()
    assert CargoSection.cargo_tons_for_ship(freighter) == pytest.approx(170.6)


def test_boxy_ore_freighter_tl9_mdrive_is_valid():
    freighter = build_boxy_ore_freighter()
    assert freighter.drives is not None
    assert freighter.drives.m_drive is not None
    assert ('error', 'Requires TL10, ship is TL8') not in [
        (note.category.value, note.message) for note in freighter.drives.m_drive.notes
    ]


def test_boxy_ore_freighter_operation_fuel_costs_80_per_month():
    freighter = build_boxy_ore_freighter()
    assert freighter.expenses.fuel == pytest.approx(80.0)

import pytest

from ceres import hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import Computer5, ComputerSection
from ceres.drives import DriveSection, FusionPlantTL8, MDrive1, PowerSection
from ceres.habitation import HabitationSection, Staterooms
from ceres.sensors import BasicSensors, SensorsSection
from ceres.storage import CargoSection, FuelSection, OperationFuel
from ceres.systems import Airlock, CommonArea, SystemsSection, Workshop

from ._markdown_output import write_markdown_output

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
        drives=DriveSection(m_drive=MDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL8(output=80)),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=12)),
        command=CommandSection(bridge=Bridge(small=True)),
        computer=ComputerSection(hardware=Computer5()),
        sensors=SensorsSection(primary=BasicSensors()),
        habitation=HabitationSection(staterooms=Staterooms(count=1), common_area=CommonArea(tons=1.0)),
        systems=SystemsSection(workshop=Workshop()),
    )


def test_boxy_ore_freighter_generates_markdown_for_visual_comparison():
    freighter = build_boxy_ore_freighter()
    table = freighter.markdown_table()
    write_markdown_output('test_boxy_ore_freighter', table)

    assert '## *Boxy* Ore Freighter | TL9 | Hull 72' in table
    assert '| Hull | Light Close Structure Hull | **200.00** |  | 6000.00 |' in table
    assert '|  | Basic Ship Systems |  | 40.00 |  |' in table
    assert '| Propulsion | M-Drive 1 | 2.00 | 20.00 | 4000.00 |' in table
    assert '| Power | Fusion (TL 8) | 8.00 | **80.00** | 4000.00 |' in table
    assert '| Fuel | 12 weeks of operation | 2.40 |  |  |' in table
    assert '| Command | Smaller Bridge | 6.00 |  | 500.00 |' in table
    assert '| Sensors | Basic |  |  |  |' in table
    assert '| Habitation | Stateroom | 4.00 |  | 500.00 |' in table
    assert '|  | Common Area | 1.00 |  | 100.00 |' in table
    assert '| Systems | Workshop | 6.00 |  | 900.00 |' in table
    assert '| Cargo | Cargo Hold | 170.60 |  |  |' in table
    assert '| Fuel | 80 |' in table


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

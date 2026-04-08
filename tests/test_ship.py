from pydantic import ValidationError
import pytest

from ceres import armour, ship
from ceres.bridge import Cockpit
from ceres.crafts import AirRaft, InternalDockingSpace
from ceres.drives import FusionPlantTL12, MDrive6
from ceres.sensors import CivilianSensors, SensorsSection
from ceres.systems import Airlock, CargoCrane, CargoHold, ProbeDrones, Workshop
from ceres.weapons import FixedFirmpoint, PulseLaser, WeaponsSection
from tests.ships._markdown_output import write_markdown_output


def test_ship_initial():
    my_ship = ship.Ship(
        tl=15,
        displacement=300,
        hull=ship.Hull(configuration=ship.sphere),
    )
    assert my_ship.tl == 15
    assert my_ship.displacement == 300
    assert my_ship.hull.configuration.points(300) == 120
    assert my_ship.cargo == 300


def test_ship_needs_hull():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(tl=15, displacement=100))


def test_ship_needs_displacement():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(tl=15, hull=ship.Hull(configuration=ship.sphere)))


def test_ship_needs_tech_level():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(hull=ship.Hull(configuration=ship.sphere), displacement=100))


def test_ship_initial_bulky():
    my_ship = ship.Ship(
        tl=15,
        displacement=100,
        hull=ship.Hull(configuration=ship.buffered_planetoid),
    )
    assert my_ship.cargo == 65


def test_ship_with_armour():
    my_ship = ship.Ship(
        tl=12,
        hull=ship.Hull(
            configuration=ship.standard_hull,
            armour=armour.CrystalironArmour(protection=4, tl=12),
        ),
        displacement=100,
    )
    assert my_ship.cargo == 100 - (100 * 4 * 0.0125)


def test_ship_cargo_subtracts_modeled_part_tonnage():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        docking_space=InternalDockingSpace(craft=AirRaft()),
        probe_drones=ProbeDrones(count=10),
        workshop=Workshop(),
    )
    assert my_ship.cargo == pytest.approx(100 - 5 - 2 - 6)


def test_ship_default_cargo_hold_uses_remaining_space():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        workshop=Workshop(),
        cargo_holds=[CargoHold()],
    )
    assert my_ship.cargo == pytest.approx(94.0)


def test_ship_explicit_cargo_hold_with_crane_reduces_usable_capacity_and_adds_cost():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=ship.Hull(configuration=ship.standard_hull),
        cargo_holds=[CargoHold(tons=150, crane=CargoCrane())],
    )
    assert my_ship.cargo == pytest.approx(147.0)
    assert my_ship.production_cost == pytest.approx(10_000_000 + 3_000_000)


def test_ship_parts_of_type_returns_matching_installed_parts():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull),
        probe_drones=ProbeDrones(count=10),
        workshop=Workshop(),
        sensors=SensorsSection(primary=CivilianSensors()),
    )
    probe_drones = my_ship.parts_of_type(ProbeDrones)
    workshops = my_ship.parts_of_type(Workshop)
    assert len(probe_drones) == 1
    assert isinstance(probe_drones[0], ProbeDrones)
    assert len(workshops) == 1
    assert isinstance(workshops[0], Workshop)


def test_ship_hull_cost():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.streamlined_hull.model_copy(update={'light': True})),
    )
    assert my_ship.hull_cost == 270_000


def test_ship_production_cost_custom_has_no_multiplier():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=ship.Hull(configuration=ship.streamlined_hull.model_copy(update={'light': True})),
        sensors=SensorsSection(primary=CivilianSensors()),
    )
    assert my_ship.production_cost == 3_270_000
    assert my_ship.sales_price_new == 3_270_000


def test_ship_sales_price_new_standard_gets_discount():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.STANDARD,
        hull=ship.Hull(configuration=ship.streamlined_hull.model_copy(update={'light': True})),
        sensors=SensorsSection(primary=CivilianSensors()),
    )
    assert my_ship.sales_price_new == 2_943_000


def test_ship_sales_price_new_new_gets_markup():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.NEW,
        hull=ship.Hull(configuration=ship.streamlined_hull.model_copy(update={'light': True})),
        sensors=SensorsSection(primary=CivilianSensors()),
    )
    assert my_ship.sales_price_new == 3_302_700


def test_ship_available_power_without_plant_is_zero():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
    )
    assert my_ship.available_power == 0


def test_ship_available_power_with_plant_uses_output():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
        fusion_plant=FusionPlantTL12(output=8),
    )
    assert my_ship.available_power == 8


def test_ship_total_power_load_includes_basic_and_active_systems():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
        m_drive=MDrive6(),
        cockpit=Cockpit(),
        sensors=SensorsSection(primary=CivilianSensors()),
        weapons=WeaponsSection(
            fixed_firmpoints=[FixedFirmpoint(weapon=PulseLaser(very_high_yield=True, energy_efficient=True))],
        ),
    )
    assert my_ship.total_power_load == 8


def test_small_craft_uses_single_pilot_crew_model():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
        cockpit=Cockpit(),
    )
    assert [(role.role, role.count, role.monthly_salary) for role in my_ship.crew_roles] == [('PILOT', 1, 6_000)]


def test_ship_with_negative_cargo_adds_local_note():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
        sensors=SensorsSection(primary=CivilianSensors()),
        workshop=Workshop(),
    )
    assert my_ship.cargo < 0
    assert [(note.category.value, note.message) for note in my_ship.notes] == [
        ('error', f'Hull overloaded by {-my_ship.cargo:.2f} tons'),
    ]


def test_markdown_table_renders_inline_error_on_cargo_row():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=ship.Hull(configuration=ship.standard_hull),
        sensors=SensorsSection(primary=CivilianSensors()),
        workshop=Workshop(),
    )
    table = my_ship.markdown_table()
    write_markdown_output('test_negative_cargo', table)
    assert '|  | **ERROR:** Hull overloaded by 1.00 tons |  |  |  |' in table


def test_ship_roundtrips_airlocks_in_parts_list():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=ship.Hull(configuration=ship.streamlined_hull, airlocks=[Airlock()]),
    )
    assert len(my_ship.parts_of_type(Airlock)) == 1

from pydantic import ValidationError
import pytest

from ceres.build.ship import armour, hull, ship
from ceres.build.ship.bridge import Bridge, Cockpit, CommandSection
from ceres.build.ship.crew import GeneralCrew, Marine, ShipCrew
from ceres.build.ship.crafts import CraftSection, InternalDockingSpace, Vehicle
from ceres.build.ship.drives import DriveSection, FusionPlantTL12, MDrive, PowerSection
from ceres.build.ship.parts import EnergyEfficient, HighTechnology
from ceres.build.ship.sensors import CivilianSensors, SensorsSection
from ceres.build.ship.storage import CargoCrane, CargoHold, CargoSection, FuelCargoContainer
from ceres.build.ship.systems import Airlock, Armoury, ProbeDrones, SystemsSection, Workshop
from ceres.build.ship.weapons import FixedMount, MountWeapon, VeryHighYield, WeaponsSection


def test_ship_initial():
    my_ship = ship.Ship(
        tl=15,
        displacement=300,
        hull=hull.Hull(configuration=hull.sphere),
    )
    assert my_ship.tl == 15
    assert my_ship.displacement == 300
    assert my_ship.hull.configuration.points(300) == 120
    assert CargoSection.cargo_tons_for_ship(my_ship) == 300


def test_ship_needs_hull():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(tl=15, displacement=100))


def test_ship_needs_displacement():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(tl=15, hull=hull.Hull(configuration=hull.sphere)))


def test_ship_needs_tech_level():
    with pytest.raises(ValidationError):
        ship.Ship.model_validate(dict(hull=hull.Hull(configuration=hull.sphere), displacement=100))


def test_ship_rejects_tl_above_16():
    with pytest.raises(ValueError, match='TL16 and lower'):
        ship.Ship(
            tl=17,
            displacement=100,
            hull=hull.Hull(configuration=hull.sphere),
        )


def test_ship_rejects_passenger_vector_list_form():
    with pytest.raises(ValidationError):
        ship.Ship(
            tl=12,
            displacement=100,
            hull=hull.Hull(configuration=hull.sphere),
            passenger_vector=[('middle', 2)],
        )


def test_ship_initial_bulky():
    my_ship = ship.Ship(
        tl=15,
        displacement=100,
        hull=hull.Hull(configuration=hull.buffered_planetoid),
    )
    assert CargoSection.cargo_tons_for_ship(my_ship) == 65


def test_ship_with_armour():
    my_ship = ship.Ship(
        tl=12,
        hull=hull.Hull(
            configuration=hull.standard_hull,
            armour=armour.CrystalironArmour(protection=4, tl=12),
        ),
        displacement=100,
    )
    assert CargoSection.cargo_tons_for_ship(my_ship) == 100 - (100 * 4 * 0.0125)


def test_ship_cargo_subtracts_modeled_part_tonnage():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        craft=CraftSection(internal_housing=[InternalDockingSpace(craft=Vehicle.from_catalog('Air/Raft'))]),
        systems=SystemsSection(internal_systems=[Workshop()], drones=[ProbeDrones(count=10)]),
    )
    assert CargoSection.cargo_tons_for_ship(my_ship) == pytest.approx(100 - 5 - 2 - 6)


def test_ship_default_cargo_hold_uses_remaining_space():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        systems=SystemsSection(internal_systems=[Workshop()]),
        cargo=CargoSection(cargo_holds=[CargoHold()]),
    )
    assert CargoSection.cargo_tons_for_ship(my_ship) == pytest.approx(94.0)


def test_ship_explicit_cargo_hold_with_crane_reduces_usable_capacity_and_adds_cost():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=150, crane=CargoCrane())]),
    )
    assert CargoSection.cargo_tons_for_ship(my_ship) == pytest.approx(147.0)
    assert my_ship.production_cost == pytest.approx(10_000_000 + 3_000_000)


def test_ship_parts_of_type_returns_matching_installed_parts():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        systems=SystemsSection(internal_systems=[Workshop()], drones=[ProbeDrones(count=10)]),
        sensors=SensorsSection(primary=CivilianSensors()),
    )
    probe_drones = my_ship.parts_of_type(ProbeDrones)
    workshops = my_ship.parts_of_type(Workshop)
    assert len(probe_drones) == 1
    assert isinstance(probe_drones[0], ProbeDrones)
    assert len(workshops) == 1
    assert isinstance(workshops[0], Workshop)


def test_military_ship_warns_when_armouries_are_below_recommendation():
    my_ship = ship.Ship(
        tl=12,
        military=True,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        crew=ShipCrew(roles=[*[GeneralCrew()] * 105, *[Marine()] * 5]),
        systems=SystemsSection(internal_systems=[Armoury(), Armoury(), Armoury(), Armoury()]),
    )

    assert ('warning', 'Installed armouries below recommendation: 4 < 5') in [
        (note.category.value, note.message) for note in my_ship.notes
    ]


def test_ship_hull_cost():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.streamlined_hull.model_copy(update={'light': True})),
    )
    assert my_ship.hull_cost == 270_000


def test_ship_production_cost_custom_has_no_multiplier():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.CUSTOM,
        hull=hull.Hull(configuration=hull.streamlined_hull.model_copy(update={'light': True})),
        sensors=SensorsSection(primary=CivilianSensors()),
    )
    assert my_ship.production_cost == 3_270_000
    assert my_ship.sales_price_new == 3_270_000


def test_ship_sales_price_new_standard_gets_discount():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(configuration=hull.streamlined_hull.model_copy(update={'light': True})),
        sensors=SensorsSection(primary=CivilianSensors()),
    )
    assert my_ship.sales_price_new == 2_943_000


def test_ship_sales_price_new_new_gets_markup():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.NEW,
        hull=hull.Hull(configuration=hull.streamlined_hull.model_copy(update={'light': True})),
        sensors=SensorsSection(primary=CivilianSensors()),
    )
    assert my_ship.sales_price_new == 3_302_700


def test_ship_available_power_without_plant_is_zero():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
    )
    assert my_ship.available_power == 0


def test_ship_available_power_with_plant_uses_output():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=8)),
    )
    assert my_ship.available_power == 8


def test_ship_basic_hull_power_load_for_non_gravity_hull_is_half():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull.model_copy(update={'non_gravity': True})),
    )
    assert my_ship.basic_hull_power_load == 0.5


def test_ship_jump_fuel_and_weapon_power_accessors_handle_missing_sections():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
    )
    assert my_ship.jump_power_load == 0.0
    assert my_ship.fuel_power_load == 0.0
    assert my_ship.weapon_power_load == 0.0


def test_ship_total_power_load_includes_basic_and_active_systems():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(m_drive=MDrive(6)),
        command=CommandSection(cockpit=Cockpit()),
        sensors=SensorsSection(primary=CivilianSensors()),
        weapons=WeaponsSection(
            fixed_mounts=[
                FixedMount(
                    weapons=[
                        MountWeapon(
                            weapon='pulse_laser',
                            customisation=HighTechnology(VeryHighYield, EnergyEfficient),
                        )
                    ]
                )
            ],
        ),
    )
    assert my_ship.total_power_load == 8


def test_ship_gets_warning_when_total_power_load_exceeds_available_power():
    my_ship = ship.Ship(
        tl=12,
        displacement=50,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
        drives=DriveSection(m_drive=MDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=10)),
        command=CommandSection(bridge=Bridge()),
        systems=SystemsSection(internal_systems=[Workshop()]),
    )

    assert ('warning', 'Capacity 5.00 less than max use') not in [
        (note.category.value, note.message) for note in my_ship.notes
    ]
    power_row = my_ship.build_spec().row('Fusion (TL 12), Power 10', section='Power')
    assert ('warning', 'Capacity 5.00 less than max use') in [
        (note.category.value, note.message) for note in power_row.notes
    ]


def test_ship_armoured_bulkhead_parts_includes_manual_bulkheads():
    bulkhead = hull.ArmouredBulkhead(protected_tonnage=10.0, protected_item='Bridge')
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull, armoured_bulkheads=[bulkhead]),
    )
    assert len(my_ship.armoured_bulkhead_parts()) == 1
    assert my_ship.armoured_bulkhead_parts()[0].protected_item == 'Bridge'


def test_small_craft_uses_single_pilot_crew_model():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        command=CommandSection(cockpit=Cockpit()),
    )
    assert [(role.role, quantity, role.monthly_salary) for role, quantity in my_ship.crew.grouped_roles] == [
        ('PILOT', 1, 6_000)
    ]


def test_ship_with_negative_cargo_adds_local_note():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=CivilianSensors()),
        systems=SystemsSection(internal_systems=[Workshop()]),
    )
    cargo_tons = CargoSection.cargo_tons_for_ship(my_ship)
    assert cargo_tons < 0
    assert ('error', f'Hull overloaded by {-cargo_tons:.2f} tons') in [
        (note.category.value, note.message) for note in my_ship.notes
    ]


def test_hull_overloaded_puts_error_on_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=CivilianSensors()),
        systems=SystemsSection(internal_systems=[Workshop()]),
    )
    assert ('error', 'Hull overloaded by 1.00 tons') in [
        (n.category.value, n.message) for n in my_ship.notes
    ]


def test_fuel_cargo_container_does_not_hide_hull_overload():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        maintained_external_displacement=120,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
        cargo=CargoSection(fuel_cargo_containers=[FuelCargoContainer(capacity=30)]),
    )

    assert ('error', 'Hull overloaded by 52.00 tons') in [
        (n.category.value, n.message) for n in my_ship.notes
    ]


def test_ship_roundtrips_airlocks_in_parts_list():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
    )
    assert len(my_ship.parts_of_type(Airlock)) == 1

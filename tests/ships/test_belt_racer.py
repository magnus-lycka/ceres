import pytest

from tycho import hull, ship
from tycho.bridge import Cockpit, CommandSection
from tycho.computer import Computer5, ComputerSection
from tycho.drives import (
    DriveSection,
    FusionPlantTL8,
    PowerSection,
    ReactionDrive,
)
from tycho.storage import CargoSection, FuelSection, ReactionFuel

from ._markdown_output import write_markdown_output

BELT_RACER_HULL = hull.close_structure.model_copy(
    update={'light': True, 'description': 'Light Close Structure Hull'},
)


def build_belt_racer() -> ship.Ship:
    return ship.Ship(
        ship_class='Vargr Belt Racer',
        ship_type='Racer',
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=BELT_RACER_HULL),
        drives=DriveSection(reaction_drive=ReactionDrive(rating=16)),
        power=PowerSection(fusion_plant=FusionPlantTL8(output=5)),
        fuel=FuelSection(reaction_fuel=ReactionFuel(minutes=52)),
        command=CommandSection(cockpit=Cockpit()),
        computer=ComputerSection(hardware=Computer5()),
    )


def test_belt_racer_matches_current_r_drive_subset():
    racer = build_belt_racer()

    assert racer.hull_cost == pytest.approx(180_000)
    assert racer.drives is not None
    assert racer.drives.reaction_drive is not None
    assert racer.drives.reaction_drive.tons == pytest.approx(1.92)
    assert racer.drives.reaction_drive.cost == pytest.approx(384_000)

    assert racer.power is not None
    assert racer.power.fusion_plant is not None
    assert racer.power.fusion_plant.tons == pytest.approx(0.5)
    assert racer.power.fusion_plant.cost == pytest.approx(250_000)

    assert racer.fuel is not None
    assert racer.fuel.reaction_fuel is not None
    assert racer.fuel.reaction_fuel.build_item() == '52 minutes of operation'
    assert racer.fuel.reaction_fuel.tons == pytest.approx(2.08)

    assert racer.command is not None
    assert racer.command.cockpit is not None
    assert racer.command.cockpit.tons == pytest.approx(1.5)
    assert racer.command.cockpit.cost == pytest.approx(10_000)

    assert racer.computer is not None
    assert racer.computer.hardware is not None
    assert racer.computer.hardware.cost == pytest.approx(30_000)

    assert racer.available_power == pytest.approx(5.0)
    assert racer.basic_hull_power_load == pytest.approx(1.0)
    assert racer.maneuver_power_load == pytest.approx(0.0)
    assert racer.sensor_power_load == pytest.approx(0.0)
    assert racer.total_power_load == pytest.approx(1.0)
    assert CargoSection.cargo_tons_for_ship(racer) == pytest.approx(0.0)
    assert racer.production_cost == pytest.approx(854_000)
    assert racer.sales_price_new == pytest.approx(854_000)
    assert racer.expenses.maintenance == pytest.approx(71.0)
    assert racer.notes == []
    assert [(role.role, role.count, role.monthly_salary) for role in racer.crew_roles] == [
        ('PILOT', 1, 6_000),
    ]


def test_belt_racer_markdown_output():
    racer = build_belt_racer()
    table = racer.markdown_table()
    write_markdown_output('test_belt_racer', table)

    assert '## *Vargr Belt Racer* Racer | TL12 | Hull 2' in table
    assert '| Hull | Light Close Structure Hull | **6.00** |  | 180.00 |' in table
    assert '| Propulsion | R-Drive Thrust 16 | 1.92 |  | 384.00 |' in table
    assert '| Power | Fusion (TL 8) | 0.50 | **5.00** | 250.00 |' in table
    assert '| Fuel | 52 minutes of operation | 2.08 |  |  |' in table
    assert '| Command | Cockpit | 1.50 |  | 10.00 |' in table
    assert '| Computer | Computer/5 |  |  | 30.00 |' in table
    assert '| Cargo | Cargo (0.00 tons) |  |  |  |' in table
    assert '-0.00' not in table
    assert 'Hull overloaded by 0.00 tons' not in table

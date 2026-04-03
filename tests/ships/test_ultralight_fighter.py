import pytest

from ceres import armour, ship
from ceres.bridge import Cockpit
from ceres.computer import Computer
from ceres.drives import FusionPlantTL12, MDrive, OperationFuel
from ceres.sensors import CivilianGradeSensors
from ceres.weapons import FixedFirmpoint, PulseLaser


def build_ultralight_fighter() -> ship.Ship:
    return ship.Ship(
        tl=12,
        displacement=6,
        design_type=ship.ShipDesignType.STANDARD,
        hull=ship.Hull(
            configuration=ship.streamlined_hull.model_copy(update={'light': True}),
            crystaliron_armour=armour.CrystalironArmour(tl=12, protection=6),
            basic_stealth=ship.BasicStealth(),
        ),
        m_drive=MDrive(rating=6, budget=True, increased_size=True),
        fusion_plant=FusionPlantTL12(
            output=8,
            budget=True,
            increased_size=True,
        ),
        operation_fuel=OperationFuel(weeks=1),
        cockpit=Cockpit(holographic=True),
        computer=Computer(rating=5),
        civilian_sensors=CivilianGradeSensors(),
        fixed_firmpoints=[
            FixedFirmpoint(
                weapon=PulseLaser(very_high_yield=True, energy_efficient=True),
            ),
        ],
    )


def test_ultralight_fighter_matches_modeled_reference_values():
    fighter = build_ultralight_fighter()
    armour_part = fighter.hull.crystaliron_armour
    stealth = fighter.hull.basic_stealth
    m_drive = fighter.m_drive
    fusion_plant = fighter.fusion_plant
    operation_fuel = fighter.operation_fuel
    cockpit = fighter.cockpit
    computer = fighter.computer
    civilian_sensors = fighter.civilian_sensors
    weapon_mount = fighter.fixed_firmpoints[0]

    assert int(fighter.tl) == 12
    assert fighter.displacement == 6

    assert armour_part is not None
    assert float(armour_part.tons) == pytest.approx(2.16)
    assert int(armour_part.cost) == 432_000

    assert stealth is not None
    assert float(stealth.tons) == pytest.approx(0.12)
    assert int(stealth.cost) == 240_000

    assert m_drive is not None
    assert float(m_drive.tons) == pytest.approx(0.45)
    assert int(m_drive.cost) == 540_000
    assert int(m_drive.power) == 4

    assert fusion_plant is not None
    assert float(fusion_plant.tons) == pytest.approx(2 / 3)
    assert int(fusion_plant.cost) == 400_000

    assert operation_fuel is not None
    assert float(operation_fuel.tons) == pytest.approx(0.02)
    assert int(operation_fuel.cost) == 0

    assert cockpit is not None
    assert float(cockpit.tons) == pytest.approx(1.5)
    assert int(cockpit.cost) == 12_500

    assert computer is not None
    assert float(computer.tons) == pytest.approx(0)
    assert int(computer.cost) == 30_000

    assert civilian_sensors is not None
    assert float(civilian_sensors.tons) == pytest.approx(1)
    assert int(civilian_sensors.cost) == 3_000_000
    assert int(civilian_sensors.power) == 1

    assert float(weapon_mount.tons) == pytest.approx(0)
    assert int(weapon_mount.cost) == 1_600_000
    assert int(weapon_mount.power) == 2

    assert fighter.hull_cost == 270_000
    assert fighter.design_cost == 6_524_500
    assert fighter.discount_cost == 5_872_050
    assert fighter.available_power == 8
    assert fighter.total_power_load == 8
    assert fighter.power_margin == 0

    # The reference sheet rounds this to 0.09 tons.
    assert float(fighter.cargo) == pytest.approx(0.08333333333333393)

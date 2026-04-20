import pytest

from tycho import armour, hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer5, ComputerSection, JumpControl1
from tycho.drives import DriveSection, FusionPlantTL12, JumpDrive1, MDrive1, PowerSection
from tycho.habitation import AdvancedEntertainmentSystem, HabitationSection, LowBerths, Staterooms
from tycho.parts import Budget, IncreasedSize
from tycho.sensors import CivilianSensors, SensorsSection
from tycho.storage import CargoCrane, CargoHold, CargoSection, FuelProcessor, FuelSection, JumpFuel, OperationFuel
from tycho.systems import Airlock, CommonArea, MedicalBay, SystemsSection, Workshop



def build_revised_beowulf() -> ship.Ship:
    """
    Modeled subset of refs/RevisedBowulf.md.

    Not yet modeled from the reference:
    - cost reduction on M-drive and jump drive
    - advanced low berth pricing/details
    - passenger luggage storage / supplies rows from the export
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
        drives=DriveSection(m_drive=MDrive1(), jump_drive=JumpDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=65, customisation=Budget(IncreasedSize))),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=1),
            operation_fuel=OperationFuel(weeks=4),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge(holographic=True)),
        computer=ComputerSection(hardware=Computer5(), software=[JumpControl1()]),
        sensors=SensorsSection(primary=CivilianSensors()),
        systems=SystemsSection(medical_bay=MedicalBay(), workshop=Workshop()),
        habitation=HabitationSection(
            staterooms=Staterooms(count=10),
            low_berths=LowBerths(count=20),
            common_area=CommonArea(tons=10.0),
            entertainment=AdvancedEntertainmentSystem(quality='adequate'),
        ),
        cargo=CargoSection(cargo_holds=[CargoHold(tons=67.5, crane=CargoCrane())]),
    )


def test_revised_beowulf_matches_current_modeled_subset():
    beowulf = build_revised_beowulf()

    assert beowulf.hull_cost == pytest.approx(9_000_000)
    assert beowulf.hull_points == 72

    assert beowulf.drives is not None
    assert beowulf.drives.m_drive is not None
    assert beowulf.drives.m_drive.tons == pytest.approx(2.0)
    assert beowulf.drives.m_drive.cost == pytest.approx(4_000_000)

    assert beowulf.drives.jump_drive is not None
    assert beowulf.drives.jump_drive.tons == pytest.approx(10.0)
    assert beowulf.drives.jump_drive.cost == pytest.approx(15_000_000)

    assert beowulf.power is not None
    assert beowulf.power.fusion_plant is not None
    assert beowulf.power.fusion_plant.tons == pytest.approx(5.4166666667)
    assert beowulf.power.fusion_plant.cost == pytest.approx(3_250_000)

    assert beowulf.fuel is not None
    assert beowulf.fuel.jump_fuel is not None
    assert beowulf.fuel.jump_fuel.tons == pytest.approx(20.0)
    assert beowulf.fuel.operation_fuel is not None
    assert beowulf.fuel.operation_fuel.tons == pytest.approx(0.55)
    assert beowulf.fuel.fuel_processor is not None
    assert beowulf.fuel.fuel_processor.tons == pytest.approx(1.0)
    assert beowulf.fuel.fuel_processor.cost == pytest.approx(50_000)

    assert beowulf.command is not None
    assert beowulf.command.bridge is not None
    assert beowulf.command.bridge.tons == pytest.approx(10.0)
    assert beowulf.command.bridge.cost == pytest.approx(1_250_000)

    assert beowulf.habitation is not None
    assert beowulf.habitation.low_berths is not None
    assert beowulf.habitation.low_berths.tons == pytest.approx(10.0)
    assert beowulf.habitation.low_berths.cost == pytest.approx(1_000_000)
    assert beowulf.habitation.entertainment is not None
    assert beowulf.habitation.entertainment.cost == pytest.approx(1_250.0)

    assert beowulf.available_power == pytest.approx(65.0)
    assert beowulf.basic_hull_power_load == pytest.approx(40.0)
    assert beowulf.jump_power_load == pytest.approx(20.0)
    assert beowulf.maneuver_power_load == pytest.approx(20.0)
    assert beowulf.sensor_power_load == pytest.approx(1.0)
    assert beowulf.weapon_power_load == pytest.approx(0.0)
    assert beowulf.fuel_power_load == pytest.approx(1.0)
    assert beowulf.total_power_load == pytest.approx(65.0)

    assert CargoSection.cargo_tons_for_ship(beowulf) == pytest.approx(64.5)
    assert beowulf.production_cost == pytest.approx(49_781_250)
    assert beowulf.sales_price_new == pytest.approx(44_803_125)
    assert beowulf.expenses.maintenance == pytest.approx(3734.0)


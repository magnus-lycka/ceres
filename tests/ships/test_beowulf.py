import pytest

from ceres import armour, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import Computer5, ComputerSection, JumpControl1
from ceres.drives import FusionPlantTL12, JumpDrive1, MDrive1
from ceres.habitation import HabitationSection, LowBerths, Staterooms
from ceres.sensors import CivilianSensors, SensorsSection
from ceres.storage import CargoCrane, CargoHold, FuelProcessor, FuelSection, JumpFuel, OperationFuel
from ceres.systems import Airlock, CommonArea

from ._markdown_output import write_markdown_output


def build_beowulf() -> ship.Ship:
    return ship.Ship(
        ship_class='Beowulf',
        ship_type='Type A Free Trader',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=ship.Hull(
            configuration=ship.streamlined_hull,
            armour=armour.CrystalironArmour(protection=2),
            airlocks=[Airlock(), Airlock()],
        ),
        m_drive=MDrive1(),
        jump_drive=JumpDrive1(),
        fusion_plant=FusionPlantTL12(output=75),
        fuel=FuelSection(
            jump_fuel=JumpFuel(parsecs=1),
            operation_fuel=OperationFuel(weeks=4),
            fuel_processor=FuelProcessor(tons=1),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5(), software=[JumpControl1()]),
        sensors=SensorsSection(primary=CivilianSensors()),
        habitation=HabitationSection(
            staterooms=Staterooms(count=10),
            low_berths=LowBerths(count=20),
            common_area=CommonArea(tons=10.0),
        ),
        cargo_holds=[CargoHold(crane=CargoCrane())],
    )


def test_beowulf_hull():
    beowulf = build_beowulf()
    assert beowulf.hull_cost == 12_000_000
    assert beowulf.hull_points == 80


def test_beowulf_armour():
    beowulf = build_beowulf()
    a = beowulf.hull.armour
    assert a is not None
    assert a.tons == pytest.approx(6.0)
    assert a.cost == 1_200_000


def test_beowulf_drives():
    beowulf = build_beowulf()
    assert beowulf.m_drive is not None
    assert beowulf.m_drive.tons == pytest.approx(2.0)
    assert beowulf.m_drive.cost == 4_000_000
    assert beowulf.m_drive.power == 20

    assert beowulf.jump_drive is not None
    assert beowulf.jump_drive.tons == pytest.approx(10.0)
    assert beowulf.jump_drive.cost == 15_000_000
    assert beowulf.jump_drive.power == 20


def test_beowulf_fusion_plant():
    beowulf = build_beowulf()
    fp = beowulf.fusion_plant
    assert fp is not None
    assert fp.output == 75
    assert fp.tons == pytest.approx(5.0)
    assert fp.cost == 5_000_000


def test_beowulf_fuel():
    beowulf = build_beowulf()
    assert beowulf.jump_fuel is not None
    assert beowulf.jump_fuel.tons == pytest.approx(20.0)
    assert beowulf.operation_fuel is not None
    assert beowulf.operation_fuel.tons == pytest.approx(0.50)
    assert beowulf.fuel_processor is not None
    assert beowulf.fuel_processor.tons == pytest.approx(1.0)
    assert beowulf.fuel_processor.cost == 50_000


def test_beowulf_bridge():
    beowulf = build_beowulf()
    b = beowulf.bridge
    assert b is not None
    assert b.tons == pytest.approx(10.0)
    assert b.cost == 1_000_000


def test_beowulf_staterooms():
    beowulf = build_beowulf()
    assert beowulf.habitation is not None
    assert beowulf.habitation.staterooms is not None
    assert beowulf.habitation.staterooms.count == 10
    assert beowulf.habitation.staterooms.tons == pytest.approx(40.0)
    assert beowulf.habitation.staterooms.cost == 5_000_000

    assert beowulf.habitation.low_berths is not None
    assert beowulf.habitation.low_berths.count == 20
    assert beowulf.habitation.low_berths.tons == pytest.approx(10.0)
    assert beowulf.habitation.low_berths.cost == 1_000_000
    assert beowulf.habitation.low_berths.power == 2


def test_beowulf_systems():
    beowulf = build_beowulf()
    assert beowulf.habitation is not None
    assert beowulf.habitation.common_area is not None
    assert beowulf.habitation.common_area.tons == pytest.approx(10.0)
    assert beowulf.fuel_scoops is not None
    assert beowulf.fuel_scoops.cost == 0.0


def test_beowulf_airlocks_free():
    # 200t ship gets 2 free airlocks
    beowulf = build_beowulf()
    assert len(beowulf.hull.airlocks) == 2
    assert beowulf.hull.airlocks[0].tons == 0.0
    assert beowulf.hull.airlocks[1].tons == 0.0


def test_beowulf_cargo():
    # Anderson shows 80.0t cargo + 0.80 luggage + 0.70 stores = 81.50t.
    # We don't model luggage or stores, so we get ~81.50t total.
    beowulf = build_beowulf()
    assert beowulf.cargo == pytest.approx(81.5, abs=0.01)


def test_beowulf_power():
    beowulf = build_beowulf()
    assert beowulf.available_power == 75
    assert beowulf.basic_hull_power_load == pytest.approx(40.0)
    assert beowulf.maneuver_power_load == 20
    assert beowulf.jump_power_load == 20
    # non-drive: sensors(1) + fuel_processor(1) + low_berths(2) = 4
    assert beowulf.total_power_load == pytest.approx(64.0)


def test_beowulf_production_cost():
    beowulf = build_beowulf()
    assert beowulf.production_cost == pytest.approx(51_380_000)
    assert beowulf.sales_price_new == pytest.approx(46_242_000)


def test_beowulf_spec_structure():
    beowulf = build_beowulf()
    spec = beowulf.build_spec()

    assert spec.ship_class == 'Beowulf'
    assert spec.ship_type == 'Type A Free Trader'
    assert spec.tl == 12
    assert spec.hull_points == 80

    assert spec.row('Streamlined Hull').section == 'Hull'
    assert spec.row('Bridge').section == 'Command'
    assert spec.row('Jump 1').section == 'Jump'
    assert spec.row('M-Drive 1').section == 'Propulsion'
    assert spec.row('Fusion (TL 12)').section == 'Power'
    assert spec.row('J-1, 4 weeks of operation').section == 'Fuel'
    assert spec.row('Fuel Scoops').section == 'Fuel'
    assert spec.row('2x Airlock').section == 'Hull'
    assert spec.row('Staterooms').section == 'Habitation'
    assert spec.row('Low Berths').section == 'Habitation'
    assert spec.row('Common Area').section == 'Habitation'
    assert spec.row('Cargo Hold').section == 'Cargo'
    assert spec.row('Cargo Crane').section == 'Cargo'

    assert spec.expenses[0].label == 'Production Cost'
    assert spec.expenses[0].amount == pytest.approx(51_380_000)
    assert spec.expenses[1].amount == pytest.approx(46_242_000)


def test_beowulf_markdown_output():
    beowulf = build_beowulf()
    table = beowulf.markdown_table()
    write_markdown_output('test_beowulf', table)

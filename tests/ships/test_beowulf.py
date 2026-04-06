import pytest

from ceres import armour, ship
from ceres.bridge import Bridge
from ceres.computer import Computer5, JumpControl1
from ceres.drives import FuelProcessor, FusionPlantTL12, JumpDrive1, JumpFuel, MDrive1, OperationFuel
from ceres.habitation import LowBerths, Staterooms
from ceres.sensors import CivilianSensors
from ceres.systems import Airlock, CargoHold, CargoCrane, CommonArea, MedicalBay, Workshop
from ceres.weapons import DoubleTurret

from ._markdown_output import write_markdown_output

light_streamlined = ship.HullConfiguration(
    description='Streamlined-Wedge, Light Hull',
    streamlined=ship.Streamlined.YES,
    armour_volume_modifier=1.2,
    hull_cost_modifier=1.2,
    light=True,
)


def build_beowulf() -> ship.Ship:
    return ship.Ship(
        ship_class='Beowulf',
        ship_type='Free Trader',
        tl=12,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=ship.Hull(
            configuration=light_streamlined,
            armour=armour.CrystalironArmour(protection=2),
        ),
        m_drive=MDrive1(),
        jump_drive=JumpDrive1(),
        fusion_plant=FusionPlantTL12(output=65, budget=True, increased_size=True),
        jump_fuel=JumpFuel(parsecs=1),
        operation_fuel=OperationFuel(weeks=4),
        fuel_processor=FuelProcessor(tons=1),
        bridge=Bridge(holographic=True),
        computer=Computer5(),
        software=[JumpControl1()],
        sensors=CivilianSensors(),
        turrets=[DoubleTurret(), DoubleTurret()],
        staterooms=Staterooms(count=10),
        low_berths=LowBerths(count=20),
        common_area=CommonArea(tons=10.0),
        medical_bay=MedicalBay(),
        workshop=Workshop(),
        airlocks=[Airlock(), Airlock()],
        cargo_holds=[CargoHold(crane=CargoCrane())],
    )


def test_beowulf_hull():
    beowulf = build_beowulf()
    assert beowulf.hull_cost == 9_000_000
    assert beowulf.hull_points == 72


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
    assert fp.output == 65
    assert fp.tons == pytest.approx(65 / 15 * 1.25)
    assert fp.cost == pytest.approx(3_250_000)


def test_beowulf_fuel():
    beowulf = build_beowulf()
    assert beowulf.jump_fuel is not None
    assert beowulf.jump_fuel.tons == pytest.approx(20.0)
    assert beowulf.operation_fuel is not None
    assert beowulf.operation_fuel.tons == pytest.approx(0.55)
    assert beowulf.fuel_processor is not None
    assert beowulf.fuel_processor.tons == pytest.approx(1.0)
    assert beowulf.fuel_processor.cost == 50_000


def test_beowulf_bridge_holographic():
    beowulf = build_beowulf()
    b = beowulf.bridge
    assert b is not None
    assert b.tons == pytest.approx(10.0)
    assert b.cost == pytest.approx(1_250_000)
    assert b.build_item() == 'Bridge (Holographic)'


def test_beowulf_staterooms():
    beowulf = build_beowulf()
    assert beowulf.staterooms is not None
    assert beowulf.staterooms.count == 10
    assert beowulf.staterooms.tons == pytest.approx(40.0)

    assert beowulf.low_berths is not None
    assert beowulf.low_berths.count == 20
    assert beowulf.low_berths.tons == pytest.approx(10.0)
    assert beowulf.low_berths.power == 2


def test_beowulf_systems():
    beowulf = build_beowulf()
    assert beowulf.medical_bay is not None
    assert beowulf.medical_bay.tons == pytest.approx(4.0)
    assert beowulf.medical_bay.cost == 2_000_000
    assert beowulf.medical_bay.power == 1.0

    assert beowulf.workshop is not None
    assert beowulf.workshop.tons == pytest.approx(6.0)

    assert beowulf.common_area is not None
    assert beowulf.common_area.tons == pytest.approx(10.0)

    assert beowulf.fuel_scoops is not None
    assert beowulf.fuel_scoops.tons == 0.0
    assert beowulf.fuel_scoops.cost == 0.0


def test_beowulf_airlocks_free():
    beowulf = build_beowulf()
    # 200t ship gets 2 free airlocks
    assert len(beowulf.airlocks) == 2
    assert beowulf.airlocks[0].tons == 0.0
    assert beowulf.airlocks[1].tons == 0.0


def test_beowulf_cargo():
    # Anderson shows 67.50t cargo (excludes passenger storage 0.80 and stores 0.74).
    # We don't model either, so we get ~1.54t more: approx 69.03t.
    beowulf = build_beowulf()
    assert beowulf.cargo == pytest.approx(69.03333, abs=0.01)


def test_beowulf_power():
    beowulf = build_beowulf()
    assert beowulf.available_power == 65
    assert beowulf.basic_hull_power_load == pytest.approx(40.0)
    assert beowulf.maneuver_power_load == 20
    assert beowulf.jump_power_load == 20
    # non-drive: sensors(1) + fuel_processor(1) + 2x turret(2) + medical(1) + low_berths(2) = 7
    assert beowulf.total_power_load == pytest.approx(67.0)


def test_beowulf_production_cost():
    beowulf = build_beowulf()
    assert beowulf.production_cost == pytest.approx(50_780_000)
    assert beowulf.sales_price_new == pytest.approx(45_702_000)


def test_beowulf_markdown_table():
    beowulf = build_beowulf()
    table = beowulf.markdown_table()
    write_markdown_output('test_beowulf', table)

    assert '## *Beowulf* Free Trader | TL12 | Hull 72' in table
    assert '| Hull | Streamlined-Wedge, Light Hull | **200.00** |  | 9000.00 |' in table
    assert '|  | Basic Ship Systems |  | 40.00 |  |' in table
    assert '| Bridge | Bridge (Holographic) | 10.00 |  | 1250.00 |' in table
    assert '| J-Drive | Jump 1 | 10.00 | 20.00 | 15000.00 |' in table
    assert '|  | Low Berths | 10.00 | 2.00 | 1000.00 |' in table
    assert '|  | Medical Bay | 4.00 | 1.00 | 2000.00 |' in table
    assert '|  | Fuel Scoops |  |  |  |' in table
    assert '| Cargo |' in table
    assert '| Cargo Crane |' in table

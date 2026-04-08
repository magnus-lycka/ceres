import pytest

from ceres import armour, hull, ship
from ceres.bridge import Bridge, CommandSection
from ceres.computer import AutoRepair1, Computer35, ComputerSection, Evade2, FireControl2
from ceres.drives import FusionPlantTL12, MDrive9
from ceres.habitation import HabitationSection, Staterooms
from ceres.sensors import CountermeasuresSuite, ImprovedSensors, SensorsSection
from ceres.storage import FuelProcessor, FuelScoops, FuelSection, OperationFuel
from ceres.systems import Airlock, CommonArea, MedicalBay, RepairDrones, SystemsSection
from ceres.weapons import MissileStorage, TripleTurret, TurretBeamLaser, TurretMissileRack, WeaponsSection

from ._markdown_output import write_markdown_output

STRANDBELL_HULL = hull.standard_hull.model_copy(
    update={'reinforced': True, 'description': 'Standard Reinforced Hull'},
)


def build_strandbell() -> ship.Ship:
    return ship.Ship(
        ship_class='Strandbell',
        ship_type='System Defense Boat',
        tl=15,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=STRANDBELL_HULL,
            armour=armour.CrystalironArmour(protection=13),
            airlocks=[Airlock(), Airlock()],
        ),
        m_drive=MDrive9(armored=True),
        fusion_plant=FusionPlantTL12(output=240),
        fuel=FuelSection(
            operation_fuel=OperationFuel(weeks=12),
            fuel_processor=FuelProcessor(tons=1),
            fuel_scoops=FuelScoops(),
        ),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer35(), software=[AutoRepair1(), FireControl2(), Evade2()]),
        sensors=SensorsSection(primary=ImprovedSensors(), countermeasures=CountermeasuresSuite()),
        weapons=WeaponsSection(
            turrets=[
                TripleTurret(weapons=[TurretBeamLaser(), TurretBeamLaser(), TurretBeamLaser()]),
                TripleTurret(weapons=[TurretMissileRack(), TurretMissileRack(), TurretMissileRack()]),
            ],
            missile_storage=MissileStorage(count=240),
        ),
        systems=SystemsSection(repair_drones=RepairDrones(), medical_bay=MedicalBay()),
        habitation=HabitationSection(staterooms=Staterooms(count=15), common_area=CommonArea(tons=4.0)),
    )


def test_strandbell_hull():
    sdb = build_strandbell()
    assert sdb.hull_points == 88
    assert sdb.hull_cost == 15_000_000


def test_strandbell_armour():
    sdb = build_strandbell()
    a = sdb.hull.armour
    assert a is not None
    assert a.protection == 13
    assert a.tons == pytest.approx(32.5)
    assert a.cost == 6_500_000


def test_strandbell_armored_m_drive():
    sdb = build_strandbell()
    assert sdb.m_drive is not None
    assert sdb.m_drive.tons == pytest.approx(19.8)
    assert sdb.m_drive.cost == pytest.approx(36_360_000)
    assert sdb.m_drive.power == pytest.approx(180)


def test_strandbell_fusion_plant():
    sdb = build_strandbell()
    fp = sdb.fusion_plant
    assert fp is not None
    assert fp.output == 240
    assert fp.tons == pytest.approx(16.0)
    assert fp.cost == 16_000_000


def test_strandbell_fuel():
    sdb = build_strandbell()
    assert sdb.operation_fuel is not None
    assert sdb.operation_fuel.tons == pytest.approx(4.8)
    assert sdb.fuel_processor is not None
    assert sdb.fuel_processor.tons == pytest.approx(1.0)
    assert sdb.fuel_processor.cost == 50_000
    assert sdb.fuel_scoops is not None
    assert sdb.fuel_scoops.cost == 1_000_000


def test_strandbell_sensors():
    sdb = build_strandbell()
    assert sdb.sensors.primary.tons == pytest.approx(3.0)
    assert sdb.sensors.primary.cost == 4_300_000
    assert sdb.sensors.primary.power == 3.0
    assert sdb.sensors.countermeasures is not None
    assert sdb.sensors.countermeasures.tons == pytest.approx(2.0)
    assert sdb.sensors.countermeasures.cost == 4_000_000
    assert sdb.sensors.countermeasures.power == 2.0


def test_strandbell_turrets():
    sdb = build_strandbell()
    assert sdb.weapons is not None
    assert len(sdb.weapons.turrets) == 2
    beam_turret = sdb.weapons.turrets[0]
    missile_turret = sdb.weapons.turrets[1]
    assert beam_turret.cost == pytest.approx(2_500_000)
    assert beam_turret.power == pytest.approx(13.0)  # 1 mount + 3 × 4 beam
    assert missile_turret.cost == pytest.approx(3_250_000)
    assert missile_turret.power == pytest.approx(1.0)  # 1 mount + 3 × 0 missiles


def test_strandbell_missile_storage():
    sdb = build_strandbell()
    assert sdb.weapons is not None
    assert sdb.weapons.missile_storage is not None
    assert sdb.weapons.missile_storage.count == 240
    assert sdb.weapons.missile_storage.tons == pytest.approx(20.0)
    assert sdb.weapons.missile_storage.cost == 0


def test_strandbell_systems():
    sdb = build_strandbell()
    assert sdb.repair_drones is not None
    assert sdb.repair_drones.tons == pytest.approx(2.0)
    assert sdb.repair_drones.cost == 400_000
    assert len(sdb.hull.airlocks) == 2
    assert sdb.hull.airlocks[0].tons == 0.0  # 2 free for 200t
    assert sdb.hull.airlocks[1].tons == 0.0
    assert sdb.medical_bay is not None
    assert sdb.habitation is not None
    assert sdb.habitation.staterooms is not None
    assert sdb.habitation.staterooms.count == 15
    assert sdb.habitation.staterooms.tons == pytest.approx(60.0)
    assert sdb.habitation.common_area is not None
    assert sdb.habitation.common_area.tons == pytest.approx(4.0)


def test_strandbell_power():
    sdb = build_strandbell()
    assert sdb.available_power == 240
    assert sdb.basic_hull_power_load == pytest.approx(40.0)
    assert sdb.maneuver_power_load == pytest.approx(180.0)
    # sensors(3) + countermeasures(2) + beam turret(13) + missile turret(1) + medical(1) + fuel processor(1) = 21
    assert sdb.total_power_load == pytest.approx(241.0)


def test_strandbell_cargo():
    # Ref: 13.8t cargo + 2.0t stores + 3.1t armored bulkheads = 18.9t.
    # We don't model stores or armored bulkheads so cargo = 18.9t.
    sdb = build_strandbell()
    assert sdb.cargo_tons == pytest.approx(18.9, abs=0.01)


def test_strandbell_cost():
    # Ref design cost 147.13MCr includes armored bulkheads (0.62MCr) and
    # stores/spares we don't model. Our production cost: 141.26MCr.
    sdb = build_strandbell()
    assert sdb.production_cost == pytest.approx(141_260_000)


def test_strandbell_software():
    sdb = build_strandbell()
    packages = [(p.description, p.cost) for p in sdb.software_packages]
    assert ('Library', 0.0) in packages
    assert ('Manoeuvre/0', 0.0) in packages
    assert ('Intellect', 0.0) in packages
    assert ('Auto-Repair/1', 5_000_000) in packages
    assert ('Fire Control/2', 4_000_000) in packages
    assert ('Evade/2', 2_000_000) in packages


def test_strandbell_spec_structure():
    sdb = build_strandbell()
    spec = sdb.build_spec()

    assert spec.ship_class == 'Strandbell'
    assert spec.ship_type == 'System Defense Boat'
    assert spec.tl == 15
    assert spec.hull_points == 88

    assert spec.row('Standard Reinforced Hull').section == 'Hull'
    assert spec.row('Crystaliron, Armour: 13').section == 'Hull'
    assert spec.row('M-Drive 9 (Armored)').section == 'Propulsion'
    assert spec.row('Fusion (TL 12)').section == 'Power'
    assert spec.row('Fuel Scoops').section == 'Fuel'
    assert spec.row('Bridge').section == 'Command'
    assert spec.row('Computer/35').section == 'Computer'
    assert spec.row('Auto-Repair/1').section == 'Computer'
    assert spec.row('Fire Control/2').section == 'Computer'
    assert spec.row('Evade/2').section == 'Computer'
    assert spec.row('Improved').section == 'Sensors'
    assert spec.row('Countermeasures Suite').section == 'Sensors'
    assert spec.row('Triple Turret (Beam Laser)').section == 'Weapons'
    assert spec.row('Triple Turret (Missile Rack)').section == 'Weapons'
    assert spec.row('Missile Storage (240)').section == 'Weapons'
    assert spec.row('Medical Bay').section == 'Systems'
    assert spec.row('Repair Drones').section == 'Systems'
    assert spec.row('Staterooms').section == 'Habitation'
    assert spec.row('Common Area').section == 'Habitation'
    assert spec.row('2x Airlock').section == 'Hull'


def test_strandbell_markdown_output():
    sdb = build_strandbell()
    table = sdb.markdown_table()
    write_markdown_output('test_strandbell', table)

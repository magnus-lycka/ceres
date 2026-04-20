import pytest

from tycho import armour, hull, ship
from tycho.bridge import Bridge, CommandSection
from tycho.computer import AutoRepair1, Computer35, ComputerSection, Evade2, FireControl2
from tycho.drives import DriveSection, FusionPlantTL12, MDrive9, PowerSection
from tycho.habitation import HabitationSection, Staterooms
from tycho.sensors import CountermeasuresSuite, ImprovedSensors, SensorsSection
from tycho.storage import CargoSection, FuelProcessor, FuelScoops, FuelSection, OperationFuel
from tycho.systems import Airlock, CommonArea, MedicalBay, RepairDrones, SystemsSection
from tycho.weapons import MissileStorage, MountWeapon, Turret, WeaponsSection


STRANDBELL_HULL = hull.standard_hull.model_copy(
    update={'reinforced': True, 'description': 'Standard Reinforced Hull'},
)


def build_strandbell() -> ship.Ship:
    return ship.Ship(
        ship_class='Strandbell',
        ship_type='System Defense Boat',
        military=True,
        tl=15,
        displacement=200,
        design_type=ship.ShipDesignType.STANDARD,
        hull=hull.Hull(
            configuration=STRANDBELL_HULL,
            armour=armour.CrystalironArmour(protection=13),
            airlocks=[Airlock(), Airlock()],
        ),
        drives=DriveSection(m_drive=MDrive9()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=240)),
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
                Turret(
                    size='triple',
                    weapons=[
                        MountWeapon(weapon='beam_laser'),
                        MountWeapon(weapon='beam_laser'),
                        MountWeapon(weapon='beam_laser'),
                    ]
                ),
                Turret(
                    size='triple',
                    weapons=[
                        MountWeapon(weapon='missile_rack'),
                        MountWeapon(weapon='missile_rack'),
                        MountWeapon(weapon='missile_rack'),
                    ]
                ),
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
    assert sdb.drives is not None
    assert sdb.drives.m_drive is not None
    assert sdb.drives.m_drive.tons == pytest.approx(18.0)
    assert sdb.drives.m_drive.cost == pytest.approx(36_000_000)
    assert sdb.drives.m_drive.power == pytest.approx(180)


def test_strandbell_fusion_plant():
    sdb = build_strandbell()
    assert sdb.power is not None
    fp = sdb.power.fusion_plant
    assert fp is not None
    assert fp.output == 240
    assert fp.tons == pytest.approx(16.0)
    assert fp.cost == 16_000_000


def test_strandbell_fuel():
    sdb = build_strandbell()
    assert sdb.fuel is not None
    assert sdb.fuel.operation_fuel is not None
    assert sdb.fuel.operation_fuel.tons == pytest.approx(4.8)
    assert sdb.fuel.fuel_processor is not None
    assert sdb.fuel.fuel_processor.tons == pytest.approx(1.0)
    assert sdb.fuel.fuel_processor.cost == 50_000
    assert sdb.fuel.fuel_scoops is not None
    assert sdb.fuel.fuel_scoops.cost == 1_000_000


def test_strandbell_sensors():
    sdb = build_strandbell()
    assert sdb.sensors.primary.tons == pytest.approx(3.0)
    assert sdb.sensors.primary.cost == 4_300_000
    assert sdb.sensors.primary.power == 3.0
    assert sdb.sensors.countermeasures is not None
    assert sdb.sensors.countermeasures.tons == pytest.approx(2.0)
    assert sdb.sensors.countermeasures.cost == 4_000_000
    assert sdb.sensors.countermeasures.power == 1.0


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
    assert sdb.systems is not None
    assert sdb.systems.repair_drones is not None
    assert sdb.systems.repair_drones.tons == pytest.approx(2.0)
    assert sdb.systems.repair_drones.cost == 400_000
    assert len(sdb.hull.airlocks) == 2
    assert sdb.hull.airlocks[0].tons == 0.0  # 2 free for 200t
    assert sdb.hull.airlocks[1].tons == 0.0
    assert sdb.systems.medical_bay is not None
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
    # sensors(3) + countermeasures(1) + beam turret(13) + missile turret(1) + medical(1) + fuel processor(1) = 20
    assert sdb.total_power_load == pytest.approx(240.0)


def test_strandbell_cargo():
    # Ref: 13.8t cargo + 2.0t stores + 3.1t armored bulkheads = 18.9t.
    # We still do not model stores for Strandbell, and we no longer model a
    # pseudo-armored M-drive, so cargo lands higher.
    sdb = build_strandbell()
    assert CargoSection.cargo_tons_for_ship(sdb) == pytest.approx(20.7, abs=0.01)


def test_strandbell_cost():
    # Ref design cost 147.13MCr includes armored bulkheads (0.62MCr) and
    # stores/spares we don't model.
    sdb = build_strandbell()
    assert sdb.production_cost == pytest.approx(140_900_000)


def test_strandbell_software():
    sdb = build_strandbell()
    assert sdb.computer is not None
    packages = [(p.description, p.cost) for p in sdb.computer.software_packages.values()]
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
    assert spec.row('M-Drive 9').section == 'Propulsion'
    assert spec.row('Fusion (TL 12)').section == 'Power'
    assert spec.row('Fuel Scoops').section == 'Fuel'
    assert spec.row('Bridge').section == 'Command'
    assert spec.row('Computer/35').section == 'Computer'
    assert spec.row('Auto-Repair/1').section == 'Computer'
    assert spec.row('Fire Control/2').section == 'Computer'
    assert spec.row('Evade/2').section == 'Computer'
    assert spec.row('Improved Sensors').section == 'Sensors'
    assert spec.row('Countermeasures Suite').section == 'Sensors'
    assert spec.row('Triple Turret', section='Weapons').section == 'Weapons'
    assert spec.row('Missile Storage (240)').section == 'Weapons'
    assert spec.row('Medical Bay').section == 'Systems'
    assert spec.row('Repair Drones').section == 'Systems'
    stateroom_row = spec.row('Staterooms', section='Habitation')
    assert stateroom_row.section == 'Habitation'
    assert stateroom_row.quantity == 15
    assert spec.row('Common Area').section == 'Habitation'
    airlock_row = spec.row('Airlock (2 tons)', section='Hull')
    assert airlock_row.section == 'Hull'
    assert airlock_row.quantity == 2


def test_strandbell_uses_military_crew_rules():
    sdb = build_strandbell()
    assert [(role.role, role.count, role.monthly_salary) for role in sdb.crew_roles] == [
        ('CAPTAIN', 1, 10_000),
        ('PILOT', 3, 6_000),
        ('ENGINEER', 1, 4_000),
        ('MAINTENANCE', 1, 1_000),
        ('GUNNER', 4, 2_000),
        ('SENSOR OPERATOR', 3, 4_000),
        ('MEDIC', 1, 4_000),
        ('OFFICER', 1, 5_000),
    ]



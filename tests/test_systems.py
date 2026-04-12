from ceres import hull, ship
from ceres.base import ShipBase
from ceres.storage import FuelScoops, FuelSection
from ceres.systems import (
    Airlock,
    BasicAutodoc,
    Biosphere,
    CommonArea,
    CrewArmory,
    MedicalBay,
    ProbeDrones,
    RepairDrones,
    SystemsSection,
    TrainingFacility,
    Workshop,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)

    def remaining_usable_tonnage(self) -> float:
        return float(self.displacement)


def test_workshop_tons():
    w = Workshop()
    w.bind(DummyOwner(12, 100))
    assert w.tons == 6.0


def test_workshop_cost():
    w = Workshop()
    w.bind(DummyOwner(12, 100))
    assert w.cost == 900_000


def test_workshop_power_zero():
    w = Workshop()
    w.bind(DummyOwner(12, 100))
    assert w.power == 0


def test_common_area_cost():
    c = CommonArea(tons=1.0)
    c.bind(DummyOwner(12, 100))
    assert c.cost == 100_000


def test_common_area_power_zero():
    c = CommonArea(tons=1.0)
    c.bind(DummyOwner(12, 100))
    assert c.power == 0


def test_crew_armory_values():
    a = CrewArmory(capacity=25)
    a.bind(DummyOwner(12, 100))
    assert a.tons == 1.0
    assert a.cost == 250_000


def test_biosphere_values():
    b = Biosphere(tons=4.0)
    b.bind(DummyOwner(12, 100))
    assert b.cost == 800_000
    assert b.power == 4.0


def test_training_facility_values():
    t = TrainingFacility(trainees=2)
    t.bind(DummyOwner(12, 100))
    assert t.tons == 4.0
    assert t.cost == 800_000


def test_probe_drones_tons():
    p = ProbeDrones(count=10)
    p.bind(DummyOwner(12, 100))
    assert p.tons == 2.0


def test_probe_drones_cost():
    p = ProbeDrones(count=10)
    p.bind(DummyOwner(12, 100))
    assert p.cost == 1_000_000


def test_probe_drones_power_zero():
    p = ProbeDrones(count=10)
    p.bind(DummyOwner(12, 100))
    assert p.power == 0


def test_medical_bay_tons():
    m = MedicalBay()
    m.bind(DummyOwner(12, 200))
    assert m.tons == 4.0


def test_medical_bay_cost():
    m = MedicalBay()
    m.bind(DummyOwner(12, 200))
    assert m.cost == 2_000_000


def test_medical_bay_power():
    m = MedicalBay()
    m.bind(DummyOwner(12, 200))
    assert m.power == 1.0


def test_medical_bay_with_basic_autodoc_cost():
    m = MedicalBay(autodoc=BasicAutodoc())
    m.bind(DummyOwner(12, 200))
    assert m.tons == 4.0
    assert m.cost == 2_100_000.0


def test_fuel_scoops_auto_included_for_streamlined_hull():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.fuel_scoops is not None


def test_fuel_scoops_free_with_streamlined_hull():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.fuel_scoops is not None
    assert my_ship.fuel.fuel_scoops.tons == 0.0
    assert my_ship.fuel.fuel_scoops.cost == 0.0


def test_fuel_scoops_not_auto_included_for_standard_hull():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
    )
    assert my_ship.fuel is None or my_ship.fuel.fuel_scoops is None


def test_fuel_scoops_paid_when_added_to_standard_hull():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        fuel=FuelSection(fuel_scoops=FuelScoops()),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.fuel_scoops is not None
    assert my_ship.fuel.fuel_scoops.tons == 0.0
    assert my_ship.fuel.fuel_scoops.cost == 1_000_000.0


def test_fuel_scoops_explicit_on_streamlined_hull_still_free():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        fuel=FuelSection(fuel_scoops=FuelScoops()),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.fuel_scoops is not None
    assert my_ship.fuel.fuel_scoops.cost == 0.0


def test_airlock_is_free_on_100_ton_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
    )
    airlock = my_ship.hull.airlocks[0]
    assert airlock.tons == 0.0
    assert airlock.cost == 0.0


def test_airlock_costs_tonnage_and_money_on_99_ton_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
    )
    airlock = my_ship.hull.airlocks[0]
    assert airlock.tons == 2.0
    assert airlock.cost == 200_000.0


def test_systems_section_all_parts():
    systems = SystemsSection(
        crew_armory=CrewArmory(capacity=25),
        biosphere=Biosphere(tons=4.0),
        workshop=Workshop(),
        medical_bay=MedicalBay(),
        probe_drones=ProbeDrones(count=10),
        repair_drones=RepairDrones(),
        training_facility=TrainingFacility(trainees=2),
    )
    assert [type(part) for part in systems._all_parts()] == [
        CrewArmory,
        Biosphere,
        Workshop,
        MedicalBay,
        ProbeDrones,
        RepairDrones,
        TrainingFacility,
    ]

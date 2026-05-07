import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.storage import FuelScoops, FuelSection
from ceres.make.ship.systems import (
    AdvancedProbeDrones,
    Airlock,
    Armoury,
    BasicAutodoc,
    Biosphere,
    BriefingRoom,
    CommercialZone,
    CommonArea,
    HotTub,
    Laboratory,
    LibraryFacility,
    MedicalBay,
    MiningDrones,
    ProbeDrones,
    RepairDrones,
    SwimmingPool,
    SystemsSection,
    Theatre,
    TrainingFacility,
    WetBar,
    Workshop,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)

    def remaining_usable_tonnage(self) -> float:
        return float(self.displacement)


@pytest.mark.parametrize(
    ('part', 'expected_tons', 'expected_cost', 'expected_power'),
    [
        (Workshop(), 6.0, 900_000.0, 0.0),
        (Laboratory(), 4.0, 1_000_000.0, 0.0),
        (LibraryFacility(), 4.0, 4_000_000.0, 0.0),
        (BriefingRoom(), 4.0, 500_000.0, 0.0),
        (Armoury(), 1.0, 250_000.0, 0.0),
        (WetBar(), 0.0, 2_000.0, 0.0),
        (MedicalBay(), 4.0, 2_000_000.0, 1.0),
        (MedicalBay(autodoc=BasicAutodoc()), 4.0, 2_100_000.0, 1.0),
        (ProbeDrones(count=10), 2.0, 1_000_000.0, 0.0),
        (AdvancedProbeDrones(count=10), 2.0, 1_600_000.0, 0.0),
        (MiningDrones(count=10), 20.0, 2_000_000.0, 0.0),
        (TrainingFacility(trainees=2), 4.0, 800_000.0, 0.0),
    ],
)
def test_converted_system_values_are_computed_properties_not_serialized_fields(
    part, expected_tons, expected_cost, expected_power
):
    part.bind(DummyOwner(15, 400))
    assert part.tons == pytest.approx(expected_tons)
    assert part.cost == pytest.approx(expected_cost)
    assert part.power == pytest.approx(expected_power)
    assert 'tons' not in part.model_dump()
    assert 'cost' not in part.model_dump()
    assert 'power' not in part.model_dump()


@pytest.mark.parametrize(
    ('part_cls', 'data', 'expected_tons', 'expected_cost', 'expected_power'),
    [
        (Workshop, {}, 6.0, 900_000.0, 0.0),
        (Laboratory, {}, 4.0, 1_000_000.0, 0.0),
        (LibraryFacility, {}, 4.0, 4_000_000.0, 0.0),
        (BriefingRoom, {}, 4.0, 500_000.0, 0.0),
        (Armoury, {}, 1.0, 250_000.0, 0.0),
        (WetBar, {}, 0.0, 2_000.0, 0.0),
        (MedicalBay, {}, 4.0, 2_000_000.0, 1.0),
        (ProbeDrones, {'count': 10}, 2.0, 1_000_000.0, 0.0),
        (AdvancedProbeDrones, {'count': 10}, 2.0, 1_600_000.0, 0.0),
        (MiningDrones, {'count': 10}, 20.0, 2_000_000.0, 0.0),
        (TrainingFacility, {'trainees': 2}, 4.0, 800_000.0, 0.0),
    ],
)
def test_converted_system_values_ignore_stale_numeric_inputs(
    part_cls, data, expected_tons, expected_cost, expected_power
):
    part = part_cls.model_validate({'tons': 99, 'cost': 99, 'power': 99, **data})
    part.bind(DummyOwner(15, 400))
    assert part.tons == pytest.approx(expected_tons)
    assert part.cost == pytest.approx(expected_cost)
    assert part.power == pytest.approx(expected_power)


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


def test_commercial_zone_values():
    z = CommercialZone(tons=240.0)
    z.bind(DummyOwner(12, 5_000))
    assert z.cost == 48_000_000.0
    assert z.power == 1.0


def test_swimming_pool_values():
    p = SwimmingPool(tons=60.0)
    p.bind(DummyOwner(12, 5_000))
    assert p.cost == 1_200_000.0
    assert p.power == 0.0


def test_theatre_values():
    t = Theatre(tons=100.0)
    t.bind(DummyOwner(12, 5_000))
    assert t.cost == 10_000_000.0
    assert t.power == 0.0


def test_wet_bar_values():
    b = WetBar()
    b.bind(DummyOwner(12, 5_000))
    assert b.tons == 0.0
    assert b.cost == 2_000.0


def test_hot_tub_values():
    tub = HotTub(users=1)
    tub.bind(DummyOwner(12, 400))
    assert tub.tons == 0.25
    assert tub.cost == 3_000.0
    assert tub.build_item() == 'Hot Tub (1 User)'


def test_armoury_values():
    a = Armoury()
    a.bind(DummyOwner(12, 10_000))
    assert a.tons == 1.0
    assert a.cost == 250_000.0


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


def test_mining_drones_values():
    drones = MiningDrones(count=10)
    drones.bind(DummyOwner(12, 10_000))
    assert drones.tons == pytest.approx(20.0)
    assert drones.cost == pytest.approx(2_000_000.0)


def test_advanced_probe_drones_values():
    p = AdvancedProbeDrones(count=20)
    p.bind(DummyOwner(15, 400))
    assert p.tons == 4.0
    assert p.cost == 3_200_000.0
    assert p.build_item() == 'Advanced Probe Drones'


def test_laboratory_values():
    lab = Laboratory()
    lab.bind(DummyOwner(12, 100))
    assert lab.tons == 4.0
    assert lab.cost == 1_000_000.0


def test_library_facility_values():
    library = LibraryFacility()
    library.bind(DummyOwner(12, 100))
    assert library.tons == 4.0
    assert library.cost == 4_000_000.0
    assert library.build_item() == 'Library'


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


def test_airlock_is_free_on_99_ton_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
    )
    airlock = my_ship.hull.airlocks[0]
    assert airlock.tons == 2.0
    assert airlock.cost == 200_000.0


def test_airlock_is_not_free_on_40_ton_small_craft():
    my_ship = ship.Ship(
        tl=12,
        displacement=40,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
    )
    airlock = my_ship.hull.airlocks[0]
    assert airlock.tons == 2.0
    assert airlock.cost == 200_000.0


def test_ship_without_explicit_airlocks_gets_minimum_two_on_1000_tons():
    my_ship = ship.Ship(
        tl=12,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.streamlined_hull),
    )

    assert len(my_ship.hull.airlocks or []) == 2
    assert all(airlock.tons == 0.0 for airlock in my_ship.hull.airlocks or [])
    assert 'Installed airlocks below minimum recommendation: 1 < 2' not in my_ship.notes.warnings


def test_ship_with_one_airlock_on_1000_tons_gets_warning_for_too_few_airlocks():
    my_ship = ship.Ship(
        tl=12,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock()]),
    )

    assert len(my_ship.hull.airlocks or []) == 1
    assert 'Installed airlocks below minimum recommendation: 1 < 2' in my_ship.notes.warnings


def test_first_ten_airlocks_are_free_on_1000_ton_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock() for _ in range(10)]),
    )

    assert len(my_ship.hull.airlocks or []) == 10
    assert all(airlock.tons == 0.0 for airlock in my_ship.hull.airlocks or [])
    assert all(airlock.cost == 0.0 for airlock in my_ship.hull.airlocks or [])


def test_eleventh_airlock_costs_tonnage_and_money_on_1000_ton_ship():
    my_ship = ship.Ship(
        tl=12,
        displacement=1_000,
        hull=hull.Hull(configuration=hull.streamlined_hull, airlocks=[Airlock() for _ in range(11)]),
    )

    assert len(my_ship.hull.airlocks or []) == 11
    assert all(airlock.tons == 0.0 for airlock in (my_ship.hull.airlocks or [])[:10])
    assert all(airlock.cost == 0.0 for airlock in (my_ship.hull.airlocks or [])[:10])
    eleventh = (my_ship.hull.airlocks or [])[10]
    assert eleventh.tons == pytest.approx(2.0)
    assert eleventh.cost == pytest.approx(200_000.0)


def test_systems_section_all_parts():
    systems = SystemsSection(
        internal_systems=[
            Armoury(),
            Biosphere(tons=4.0),
            CommercialZone(tons=240.0),
            Workshop(),
            MedicalBay(),
            TrainingFacility(trainees=2),
        ],
        drones=[ProbeDrones(count=10), RepairDrones()],
    )
    assert [type(part) for part in systems._all_parts()] == [
        Armoury,
        Biosphere,
        CommercialZone,
        Workshop,
        MedicalBay,
        TrainingFacility,
        ProbeDrones,
        RepairDrones,
    ]

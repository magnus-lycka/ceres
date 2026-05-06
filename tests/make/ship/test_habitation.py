import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.computer import Computer5, ComputerSection
from ceres.make.ship.crew import Pilot, ShipCrew
from ceres.make.ship.drives import DriveSection, FusionPlantTL12, JDrive1, PowerSection
from ceres.make.ship.habitation import (
    AdvancedEntertainmentSystem,
    CabinSpace,
    HabitationSection,
    HighStateroom,
    LowBerth,
    LuxuryStateroom,
    Stateroom,
)
from ceres.make.ship.systems import CommonArea, SwimmingPool


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_staterooms_tons():
    s = Stateroom()
    s.bind(DummyOwner(12, 100))
    assert s.tons == pytest.approx(4.0)


def test_staterooms_cost():
    s = Stateroom()
    s.bind(DummyOwner(12, 100))
    assert s.cost == 500_000


def test_staterooms_power_zero():
    s = Stateroom()
    s.bind(DummyOwner(12, 100))
    assert s.power == 0


def test_staterooms_life_support_uses_full_occupancy_formula():
    s = Stateroom()
    s.bind(DummyOwner(12, 100))
    assert s.occupancy == 2
    assert s.life_support_cost == 3_000


def test_multiple_staterooms_add_linearly():
    rooms = [Stateroom() for _ in range(4)]
    for room in rooms:
        room.bind(DummyOwner(12, 100))
    assert sum(room.tons for room in rooms) == pytest.approx(16.0)
    assert sum(room.cost for room in rooms) == 2_000_000
    assert sum(room.occupancy for room in rooms) == 8
    assert sum(room.life_support_cost for room in rooms) == 12_000


def test_low_berths_tons():
    lb = LowBerth()
    lb.bind(DummyOwner(12, 200))
    assert lb.tons == pytest.approx(0.5)


def test_low_berths_cost():
    lb = LowBerth()
    lb.bind(DummyOwner(12, 200))
    assert lb.cost == 50_000


def test_low_berths_power():
    ship_20 = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(low_berths=[LowBerth()] * 20),
    )
    ship_1 = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(low_berths=[LowBerth()]),
    )
    ship_10 = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(low_berths=[LowBerth()] * 10),
    )
    ship_11 = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(low_berths=[LowBerth()] * 11),
    )

    assert ship_20.habitation is not None
    assert sum(berth.power for berth in ship_20.habitation.low_berths) == 2
    assert ship_1.habitation is not None
    assert sum(berth.power for berth in ship_1.habitation.low_berths) == 1
    assert ship_10.habitation is not None
    assert sum(berth.power for berth in ship_10.habitation.low_berths) == 1
    assert ship_11.habitation is not None
    assert sum(berth.power for berth in ship_11.habitation.low_berths) == 2


def test_advanced_entertainment_system_cost():
    system = AdvancedEntertainmentSystem(cost=500)
    system.bind(DummyOwner(12, 100))
    assert system.tons == 0
    assert system.cost == 500.0


def test_advanced_entertainment_system_requires_cost_in_allowed_range():
    with pytest.raises(ValueError, match='between 100 and 10000 credits'):
        AdvancedEntertainmentSystem(cost=99)


def test_cabin_space_cost():
    cabin = CabinSpace(tons=15.0)
    cabin.bind(DummyOwner(12, 100))
    assert cabin.cost == 750_000.0


def test_cabin_space_passenger_capacity():
    cabin = CabinSpace(tons=15.0)
    cabin.bind(DummyOwner(12, 100))
    assert cabin.passenger_capacity == 10


def test_cabin_space_fixed_life_support_cost():
    cabin = CabinSpace(tons=15.0)
    cabin.bind(DummyOwner(12, 100))
    assert cabin.fixed_life_support_cost == 3_750.0


def test_high_stateroom_values():
    s = HighStateroom()
    s.bind(DummyOwner(12, 100))
    assert s.label == 'High Stateroom'
    assert s.tons == pytest.approx(6.0)
    assert s.cost == pytest.approx(800_000.0)


def test_luxury_stateroom_values():
    s = LuxuryStateroom()
    s.bind(DummyOwner(12, 100))
    assert s.label == 'Luxury Stateroom'
    assert s.tons == pytest.approx(10.0)
    assert s.cost == pytest.approx(1_500_000.0)
    assert s.life_support_cost == pytest.approx(5_000.0)


def test_habitation_section_supports_standard_and_high_staterooms():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 4 + [HighStateroom()],
        ),
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.fixed_life_support_cost(my_ship) == pytest.approx(5_000.0)


def test_habitation_default_passenger_vector_uses_unused_staterooms_and_low_berths():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 10, low_berths=[LowBerth()] * 4),
        crew=ShipCrew(roles=[Pilot()] * 7),
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.default_passenger_vector(my_ship) == {
        'middle': 12,
        'low': 4,
    }


def test_habitation_default_middle_passengers_include_cabin_space_capacity():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 4, cabin_space=CabinSpace(tons=15.0)),
        crew=ShipCrew(roles=[Pilot()] * 2),
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.default_passenger_vector(my_ship) == {
        'middle': 16,
        'low': 0,
    }


def test_habitation_explicit_passenger_vector_overrides_default():
    my_ship = ship.Ship(
        tl=12,
        displacement=100,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        drives=DriveSection(j_drive=JDrive1()),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=10)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer5()),
        habitation=HabitationSection(staterooms=[Stateroom()] * 4),
        passenger_vector={'high': 1},
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.passenger_vector(my_ship) == {'high': 1}


def test_habitation_life_support_separates_fixed_and_variable_costs():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 4, cabin_space=CabinSpace(tons=15.0)),
        crew=ShipCrew(roles=[Pilot()] * 16),
        passenger_vector={},
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.fixed_life_support_cost(my_ship) == 7_750.0
    assert my_ship.habitation.variable_life_support_cost(my_ship) == 16_000.0
    assert my_ship.habitation.life_support_cost(my_ship) == 23_750.0


def test_common_area_requirement_counts_common_area_facilities_toward_total():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(
            staterooms=[Stateroom()] * 4,
            common_area=CommonArea(tons=2.0),
            swimming_pool=SwimmingPool(tons=2.0),
        ),
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.provided_common_area_tons() == pytest.approx(4.0)
    assert 'Recommended common area is 4.00 tons' not in my_ship.habitation.notes.warnings


def test_explicit_middle_passengers_must_fit_in_remaining_non_crew_beds():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 10),
        crew=ShipCrew(roles=[Pilot()] * 7),
        passenger_vector={'middle': 13},
    )

    assert my_ship.habitation is not None
    assert 'Middle passage exceeds available non-crew beds: 13 > 12' in my_ship.habitation.notes.errors


def test_explicit_low_passengers_must_fit_in_low_berths():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()], low_berths=[LowBerth()] * 4),
        crew=ShipCrew(roles=[Pilot()]),
        passenger_vector={'low': 5},
    )

    assert my_ship.habitation is not None
    assert 'Low passage exceeds available low berths: 5 > 4' in my_ship.habitation.notes.errors


def test_high_and_middle_passengers_can_exactly_fill_remaining_non_crew_staterooms():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 8),
        crew=ShipCrew(roles=[Pilot()] * 4),
        passenger_vector={'high': 4, 'middle': 4},
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.notes.errors == []


def test_one_more_high_passenger_than_capacity_errors():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 8),
        crew=ShipCrew(roles=[Pilot()] * 4),
        passenger_vector={'high': 7, 'middle': 0},
    )

    assert my_ship.habitation is not None
    assert 'High passage exceeds available non-crew staterooms: 7 > 6' in my_ship.habitation.notes.errors


def test_one_more_middle_passenger_than_capacity_errors():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 8),
        crew=ShipCrew(roles=[Pilot()] * 4),
        passenger_vector={'high': 4, 'middle': 5},
    )

    assert my_ship.habitation is not None
    assert 'Middle passage exceeds available non-crew beds: 5 > 4' in my_ship.habitation.notes.errors


def test_three_crew_three_middle_three_high_fit_in_seven_staterooms():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 7),
        crew=ShipCrew(roles=[Pilot()] * 3),
        passenger_vector={'high': 3, 'middle': 3},
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.notes.errors == []


def test_one_more_crew_still_fits_in_seven_stateroom_case():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 7),
        crew=ShipCrew(roles=[Pilot()] * 4),
        passenger_vector={'high': 3, 'middle': 3},
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.notes.errors == []


def test_one_more_middle_still_fits_in_seven_stateroom_case():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 7),
        crew=ShipCrew(roles=[Pilot()] * 3),
        passenger_vector={'high': 3, 'middle': 4},
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.notes.errors == []


def test_one_more_high_does_not_fit_even_with_spare_beds():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=[Stateroom()] * 7),
        crew=ShipCrew(roles=[Pilot()] * 3),
        passenger_vector={'high': 4, 'middle': 3},
    )

    assert my_ship.habitation is not None
    assert 'Middle passage exceeds available non-crew beds: 3 > 2' in my_ship.habitation.notes.errors

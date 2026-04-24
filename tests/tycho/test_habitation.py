import pytest

from tycho import hull, ship
from tycho.base import ShipBase
from tycho.bridge import Bridge, CommandSection
from tycho.computer import Computer, ComputerSection
from tycho.crew import Pilot, ShipCrew
from tycho.drives import DriveSection, FusionPlantTL12, JDrive, PowerSection
from tycho.habitation import AdvancedEntertainmentSystem, CabinSpace, HabitationSection, LowBerths, Staterooms


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_staterooms_tons():
    s = Staterooms(4)
    s.bind(DummyOwner(12, 100))
    assert s.tons == pytest.approx(16.0)


def test_staterooms_cost():
    s = Staterooms(4)
    s.bind(DummyOwner(12, 100))
    assert s.cost == 2_000_000


def test_staterooms_power_zero():
    s = Staterooms(4)
    s.bind(DummyOwner(12, 100))
    assert s.power == 0


def test_staterooms_life_support_uses_full_occupancy_formula():
    s = Staterooms(4)
    s.bind(DummyOwner(12, 100))
    assert s.occupancy == 8
    assert s.life_support_cost == 12_000


def test_low_berths_tons():
    lb = LowBerths(20)
    lb.bind(DummyOwner(12, 200))
    assert lb.tons == pytest.approx(10.0)


def test_low_berths_cost():
    lb = LowBerths(20)
    lb.bind(DummyOwner(12, 200))
    assert lb.cost == 1_000_000


def test_low_berths_power():
    assert LowBerths(20).compute_power() == 2  # ceil(20/10)
    assert LowBerths(1).compute_power() == 1   # ceil(1/10)
    assert LowBerths(10).compute_power() == 1
    assert LowBerths(11).compute_power() == 2


def test_advanced_entertainment_system_cost():
    system = AdvancedEntertainmentSystem(500)
    system.bind(DummyOwner(12, 100))
    assert system.tons == 0
    assert system.cost == 500.0


def test_advanced_entertainment_system_requires_cost_in_allowed_range():
    with pytest.raises(ValueError, match='between 100 and 10000 credits'):
        AdvancedEntertainmentSystem(99)


def test_cabin_space_cost():
    cabin = CabinSpace(15.0)
    cabin.bind(DummyOwner(12, 100))
    assert cabin.cost == 750_000.0


def test_cabin_space_passenger_capacity():
    cabin = CabinSpace(15.0)
    cabin.bind(DummyOwner(12, 100))
    assert cabin.passenger_capacity == 10


def test_cabin_space_fixed_life_support_cost():
    cabin = CabinSpace(15.0)
    cabin.bind(DummyOwner(12, 100))
    assert cabin.fixed_life_support_cost == 3_750.0


def test_high_stateroom_values():
    s = Staterooms(1, kind='high')
    s.bind(DummyOwner(12, 100))
    assert s.label == 'High Stateroom'
    assert s.tons == pytest.approx(6.0)
    assert s.cost == pytest.approx(800_000.0)


def test_luxury_stateroom_values():
    s = Staterooms(1, kind='luxury')
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
            staterooms=Staterooms(4),
            high_staterooms=Staterooms(1, kind='high'),
        ),
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.fixed_life_support_cost(my_ship) == pytest.approx(5_000.0)


def test_staterooms_reject_unknown_kind():
    with pytest.raises(ValueError, match='Input should be'):
        Staterooms(1, kind='penthouse')


def test_habitation_default_passenger_vector_uses_unused_staterooms_and_low_berths():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=10), low_berths=LowBerths(count=4)),
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
        habitation=HabitationSection(staterooms=Staterooms(count=4), cabin_space=CabinSpace(tons=15.0)),
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
        drives=DriveSection(j_drive=JDrive(1)),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=10)),
        command=CommandSection(bridge=Bridge()),
        computer=ComputerSection(hardware=Computer(5)),
        habitation=HabitationSection(staterooms=Staterooms(count=4)),
        passenger_vector={'high': 1},
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.passenger_vector(my_ship) == {'high': 1}


def test_habitation_life_support_separates_fixed_and_variable_costs():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=4), cabin_space=CabinSpace(tons=15.0)),
        crew=ShipCrew(roles=[Pilot()] * 16),
        passenger_vector={},
    )

    assert my_ship.habitation is not None
    assert my_ship.habitation.fixed_life_support_cost(my_ship) == 7_750.0
    assert my_ship.habitation.variable_life_support_cost(my_ship) == 16_000.0
    assert my_ship.habitation.life_support_cost(my_ship) == 23_750.0


def test_explicit_middle_passengers_must_fit_in_remaining_non_crew_beds():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=10)),
        crew=ShipCrew(roles=[Pilot()] * 7),
        passenger_vector={'middle': 13},
    )

    assert ('error', 'Middle passage exceeds available non-crew beds: 13 > 12') in [
        (note.category.value, note.message) for note in my_ship.habitation.notes
    ]


def test_explicit_low_passengers_must_fit_in_low_berths():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=1), low_berths=LowBerths(count=4)),
        crew=ShipCrew(roles=[Pilot()]),
        passenger_vector={'low': 5},
    )

    assert ('error', 'Low passage exceeds available low berths: 5 > 4') in [
        (note.category.value, note.message) for note in my_ship.habitation.notes
    ]


def test_high_and_middle_passengers_can_exactly_fill_remaining_non_crew_staterooms():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=8)),
        crew=ShipCrew(roles=[Pilot()] * 4),
        passenger_vector={'high': 4, 'middle': 4},
    )

    assert my_ship.habitation is not None
    assert [
        (note.category.value, note.message)
        for note in my_ship.habitation.notes
        if note.category.value == 'error'
    ] == []


def test_one_more_high_passenger_than_capacity_errors():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=8)),
        crew=ShipCrew(roles=[Pilot()] * 4),
        passenger_vector={'high': 7, 'middle': 0},
    )

    assert ('error', 'High passage exceeds available non-crew staterooms: 7 > 6') in [
        (note.category.value, note.message) for note in my_ship.habitation.notes
    ]


def test_one_more_middle_passenger_than_capacity_errors():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=8)),
        crew=ShipCrew(roles=[Pilot()] * 4),
        passenger_vector={'high': 4, 'middle': 5},
    )

    assert ('error', 'Middle passage exceeds available non-crew beds: 5 > 4') in [
        (note.category.value, note.message) for note in my_ship.habitation.notes
    ]


def test_three_crew_three_middle_three_high_fit_in_seven_staterooms():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=7)),
        crew=ShipCrew(roles=[Pilot()] * 3),
        passenger_vector={'high': 3, 'middle': 3},
    )

    assert my_ship.habitation is not None
    assert [
        (note.category.value, note.message)
        for note in my_ship.habitation.notes
        if note.category.value == 'error'
    ] == []


def test_one_more_crew_still_fits_in_seven_stateroom_case():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=7)),
        crew=ShipCrew(roles=[Pilot()] * 4),
        passenger_vector={'high': 3, 'middle': 3},
    )

    assert my_ship.habitation is not None
    assert [
        (note.category.value, note.message)
        for note in my_ship.habitation.notes
        if note.category.value == 'error'
    ] == []


def test_one_more_middle_still_fits_in_seven_stateroom_case():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=7)),
        crew=ShipCrew(roles=[Pilot()] * 3),
        passenger_vector={'high': 3, 'middle': 4},
    )

    assert my_ship.habitation is not None
    assert [
        (note.category.value, note.message)
        for note in my_ship.habitation.notes
        if note.category.value == 'error'
    ] == []


def test_one_more_high_does_not_fit_even_with_spare_beds():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        habitation=HabitationSection(staterooms=Staterooms(count=7)),
        crew=ShipCrew(roles=[Pilot()] * 3),
        passenger_vector={'high': 4, 'middle': 3},
    )

    assert ('error', 'Middle passage exceeds available non-crew beds: 3 > 2') in [
        (note.category.value, note.message) for note in my_ship.habitation.notes
    ]

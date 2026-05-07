from ceres.make.ship.occupants import (
    BasicPassage,
    Crew,
    FrozenWatch,
    Guest,
    HighPassage,
    LowPassage,
    MiddlePassage,
    Officer,
    Owner,
    ResidenceAllocator,
    ResidenceDemand,
    Troop,
)


class RoomOneBed:
    provides = [
        (ResidenceDemand.CREW_STATEROOM, 1),
        (ResidenceDemand.PASSENGER_STATEROOM, 1),
    ]


class RoomTwoBeds:
    provides = [
        (ResidenceDemand.CREW_STATEROOM, 1),
        (ResidenceDemand.PASSENGER_STATEROOM, 1),
        (ResidenceDemand.CREW_STATEROOM_BED, 2),
        (ResidenceDemand.ANY_CREW_BED, 2),
        (ResidenceDemand.PASSENGER_STATEROOM_BED, 2),
    ]


def test_high_passage_requirements():
    assert HighPassage.demand == ResidenceDemand.PASSENGER_STATEROOM


def test_middle_passage_requirements():
    assert MiddlePassage.demand == ResidenceDemand.PASSENGER_STATEROOM_BED


def test_basic_passage_requirements():
    assert BasicPassage.demand == ResidenceDemand.ANYTHING


def test_low_passage_requirements():
    assert LowPassage.demand == ResidenceDemand.LOW_BERTH


def test_owner_requirements():
    assert Owner.demand == ResidenceDemand.PASSENGER_STATEROOM


def test_guest_requirements():
    assert Guest.demand == ResidenceDemand.PASSENGER_STATEROOM_BED


def test_officer_requirements():
    assert Officer.demand == ResidenceDemand.CREW_STATEROOM


def test_crew_requirements():
    assert Crew.demand == ResidenceDemand.CREW_STATEROOM_BED


def test_frozen_watch_requirements():
    assert FrozenWatch.demand == ResidenceDemand.LOW_BERTH


def test_troop_requirements():
    assert Troop.demand == ResidenceDemand.ANY_CREW_BED


def test_allocator_provides_hp_stateroom():
    allocator = ResidenceAllocator(residences=[RoomOneBed()])
    hp, mp = HighPassage(), MiddlePassage()
    provided, rejected = allocator.provide_reject([hp, mp])
    assert provided == [hp]
    assert rejected == [mp]


def test_allocator_bp_gets_nothing():
    allocator = ResidenceAllocator(residences=[RoomOneBed()])
    bp1, hp, mp, bp2 = BasicPassage(), HighPassage(), MiddlePassage(), BasicPassage()
    provided, rejected = allocator.provide_reject([bp1, hp, mp, bp2])
    assert provided == [bp1, hp, bp2]
    assert rejected == [mp]


def test_allocator_provides_mps_stateroom():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    mp1, mp2 = MiddlePassage(), MiddlePassage()
    provided, rejected = allocator.provide_reject([mp1, mp2])
    assert provided == [mp1, mp2]
    assert rejected == []


def test_allocator_hp_grabs_whole_stateroom():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    hp, mp = HighPassage(), MiddlePassage()
    provided, rejected = allocator.provide_reject([hp, mp])
    assert provided == [hp]
    assert rejected == [mp]


def test_allocator_owner_uses_high_passage_accommodation():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    owner, guest = Owner(), Guest()
    provided, rejected = allocator.provide_reject([owner, guest])
    assert provided == [owner]
    assert rejected == [guest]


def test_allocator_guest_uses_middle_passage_accommodation():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    guest1, guest2 = Guest(), Guest()
    provided, rejected = allocator.provide_reject([guest1, guest2])
    assert provided == [guest1, guest2]
    assert rejected == []


def test_allocator_frozen_watch_uses_low_berth():
    allocator = ResidenceAllocator(residences=[RoomOneBed()])
    frozen_watch = FrozenWatch()
    provided, rejected = allocator.provide_reject([frozen_watch])
    assert provided == []
    assert rejected == [frozen_watch]


def test_ship_occupants_are_individual_objects():
    middle_passengers = [MiddlePassage(), MiddlePassage(), MiddlePassage()]
    assert len(middle_passengers) == 3
    assert [passenger.kind for passenger in middle_passengers] == ['middle', 'middle', 'middle']
    assert all(not hasattr(passenger, 'count') for passenger in middle_passengers)


def test_allocator_provides_right_stateroom_to_mix():
    allocator = ResidenceAllocator(residences=[RoomOneBed(), RoomTwoBeds(), RoomTwoBeds()])
    mp1 = MiddlePassage()
    mp2 = MiddlePassage()
    mp3 = MiddlePassage()
    hp = HighPassage()
    c1 = Crew()
    c2 = Crew()
    c3 = Crew()
    provided, rejected = allocator.provide_reject([mp1, hp, c1, mp2, mp3, c2, c3])
    assert provided == [mp1, hp, c1, mp2, c2]
    assert rejected == [mp3, c3]

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


class LowBerthResidence:
    provides = [(ResidenceDemand.LOW_BERTH, 1)]


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
    allocator = ResidenceAllocator(residences=[LowBerthResidence()])
    frozen_watch = FrozenWatch()
    provided, rejected = allocator.provide_reject([frozen_watch])
    assert provided == [frozen_watch]
    assert rejected == []


def test_allocator_low_passage_uses_low_berth():
    allocator = ResidenceAllocator(residences=[LowBerthResidence()])
    low = LowPassage()
    provided, rejected = allocator.provide_reject([low])
    assert provided == [low]
    assert rejected == []


def test_allocator_officer_uses_crew_stateroom_and_blocks_crew_beds():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    officer, crew = Officer(), Crew()
    provided, rejected = allocator.provide_reject([officer, crew])
    assert provided == [officer]
    assert rejected == [crew]


def test_allocator_crew_uses_crew_stateroom_beds():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    crew1, crew2 = Crew(), Crew()
    provided, rejected = allocator.provide_reject([crew1, crew2])
    assert provided == [crew1, crew2]
    assert rejected == []


def test_allocator_troop_uses_any_crew_bed():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    troop1, troop2 = Troop(), Troop()
    provided, rejected = allocator.provide_reject([troop1, troop2])
    assert provided == [troop1, troop2]
    assert rejected == []


def test_allocator_crew_and_troop_share_crew_bed_capacity():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    crew, troop = Crew(), Troop()
    provided, rejected = allocator.provide_reject([crew, troop])
    assert provided == [crew, troop]
    assert rejected == []


def test_allocator_passenger_bed_excludes_later_crew_bed_use():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    middle, crew = MiddlePassage(), Crew()
    provided, rejected = allocator.provide_reject([middle, crew])
    assert provided == [middle]
    assert rejected == [crew]


def test_allocator_crew_bed_excludes_later_passenger_bed_use():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds()])
    troop, middle = Troop(), MiddlePassage()
    provided, rejected = allocator.provide_reject([troop, middle])
    assert provided == [troop]
    assert rejected == [middle]


def test_allocator_high_passage_prefers_single_stateroom_before_double_room():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds(), RoomOneBed()])
    high, middle = HighPassage(), MiddlePassage()
    provided, rejected = allocator.provide_reject([high, middle])
    assert provided == [high, middle]
    assert rejected == []


def test_allocator_officer_prefers_single_stateroom_before_double_room():
    allocator = ResidenceAllocator(residences=[RoomTwoBeds(), RoomOneBed()])
    officer, crew = Officer(), Crew()
    provided, rejected = allocator.provide_reject([officer, crew])
    assert provided == [officer, crew]
    assert rejected == []


def test_allocator_mixed_crew_and_passenger_demands_keep_existing_priority():
    allocator = ResidenceAllocator(
        residences=[RoomOneBed(), RoomTwoBeds(), RoomTwoBeds(), RoomTwoBeds(), RoomTwoBeds(), LowBerthResidence()]
    )
    officer = Officer()
    high = HighPassage()
    crew1 = Crew()
    crew2 = Crew()
    crew3 = Crew()
    middle = MiddlePassage()
    low = LowPassage()
    provided, rejected = allocator.provide_reject([officer, high, crew1, middle, crew2, crew3, low])
    assert provided == [officer, high, crew1, middle, crew2, crew3, low]
    assert rejected == []


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

import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.bridge import Bridge, CommandSection
from ceres.make.ship.habitation import HabitationSection
from ceres.make.ship.storage import FuelScoops, FuelSection
from ceres.make.ship.systems import (
    AccelerationBench,
    AccelerationSeat,
    AdvancedProbeDrones,
    AdvancedPsionicShielding,
    Aerofins,
    Airlock,
    Armoury,
    AssaultReEntryCapsule,
    BasicAutodoc,
    BasicReEntryCapsule,
    Biosphere,
    BoobyTrapTL6,
    BoobyTrapTL8,
    BoobyTrapTL10,
    BoobyTrapTL12,
    BreachingTube,
    Brewery,
    BriefingRoom,
    CommandBridge,
    CommercialZone,
    CommonArea,
    ConstructionDeck,
    ForcedLinkageApparatus,
    GourmetKitchen,
    GravityWellGenerator,
    GravScreen,
    HighSurvivabilityReEntryCapsule,
    HolographicHull,
    HotTub,
    JumpFilter,
    Laboratory,
    LibraryFacility,
    MedicalBay,
    MiningDrones,
    MultiEnvironmentSpace,
    ProbeDrones,
    PsionicShielding,
    ReEntryPod,
    RepairDrones,
    SwimmingPool,
    SystemsSection,
    Theatre,
    TrainingFacility,
    UNREPSystem,
    Vault,
    WetBar,
    Workshop,
    ZeroGRoom,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)

    def remaining_usable_tonnage(self) -> float:
        return float(self.displacement)


def _dummy_owner_for(part) -> DummyOwner:
    if isinstance(part, Airlock):
        return DummyOwner(15, 99)
    return DummyOwner(15, 400)


@pytest.mark.parametrize(
    ('part', 'expected_tons', 'expected_cost', 'expected_power'),
    [
        (Workshop(), 6.0, 900_000.0, 0.0),
        (Laboratory(), 4.0, 1_000_000.0, 0.0),
        (LibraryFacility(), 4.0, 4_000_000.0, 0.0),
        (BriefingRoom(), 4.0, 500_000.0, 0.0),
        (CommandBridge(), 40.0, 30_000_000.0, 0.0),
        (Armoury(), 1.0, 250_000.0, 0.0),
        (WetBar(), 0.0, 2_000.0, 0.0),
        (MedicalBay(), 4.0, 2_000_000.0, 1.0),
        (MedicalBay(autodoc=BasicAutodoc()), 4.0, 2_100_000.0, 1.0),
        (GravScreen(), 2.0, 2_000_000.0, 4.0),
        (GravityWellGenerator(), 100.0, 120_000_000.0, 500.0),
        (JumpFilter(), 0.0, 5_000_000.0, 1.0),
        (PsionicShielding(), 4.0, 2_000_000.0, 0.0),
        (AdvancedPsionicShielding(), 0.0, 4_000_000.0, 0.0),
        (AccelerationBench(), 1.0, 10_000.0, 0.0),
        (AccelerationSeat(), 0.5, 30_000.0, 0.0),
        (Brewery(litres_per_week=20), 1.0, 100_000.0, 0.0),
        (GourmetKitchen(diners=4), 4.0, 800_000.0, 0.0),
        (BasicReEntryCapsule(), 0.5, 20_000.0, 0.0),
        (AssaultReEntryCapsule(), 0.5, 50_000.0, 0.0),
        (HighSurvivabilityReEntryCapsule(), 0.5, 100_000.0, 0.0),
        (ReEntryPod(), 1.0, 150_000.0, 0.0),
        (Airlock(size=3.0), 3.0, 300_000.0, 0.0),
        (Aerofins(), 20.0, 2_000_000.0, 0.0),
        (BreachingTube(), 3.0, 3_000_000.0, 0.0),
        (ForcedLinkageApparatus(tier='Basic'), 2.0, 50_000.0, 0.0),
        (ForcedLinkageApparatus(tier='Improved'), 2.0, 75_000.0, 0.0),
        (ForcedLinkageApparatus(tier='Enhanced'), 2.0, 100_000.0, 0.0),
        (ForcedLinkageApparatus(tier='Advanced'), 2.0, 500_000.0, 0.0),
        (HolographicHull(), 0.0, 40_000_000.0, 200.0),
        (HotTub(users=2), 0.5, 6_000.0, 0.0),
        (ProbeDrones(count=10), 2.0, 1_000_000.0, 0.0),
        (AdvancedProbeDrones(count=10), 2.0, 1_600_000.0, 0.0),
        (RepairDrones(), 4.0, 800_000.0, 0.0),
        (MiningDrones(count=10), 20.0, 2_000_000.0, 0.0),
        (TrainingFacility(trainees=2), 4.0, 800_000.0, 0.0),
    ],
)
def test_converted_system_values_are_computed_properties_not_serialized_fields(
    part, expected_tons, expected_cost, expected_power
):
    part.bind(_dummy_owner_for(part))
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
        (CommandBridge, {}, 40.0, 30_000_000.0, 0.0),
        (ConstructionDeck, {'tons': 100.0}, 100.0, 50_000_000.0, 100.0),
        (Armoury, {}, 1.0, 250_000.0, 0.0),
        (WetBar, {}, 0.0, 2_000.0, 0.0),
        (MedicalBay, {}, 4.0, 2_000_000.0, 1.0),
        (GravScreen, {}, 2.0, 2_000_000.0, 4.0),
        (GravityWellGenerator, {}, 100.0, 120_000_000.0, 500.0),
        (JumpFilter, {}, 0.0, 5_000_000.0, 1.0),
        (PsionicShielding, {}, 4.0, 2_000_000.0, 0.0),
        (AdvancedPsionicShielding, {}, 0.0, 4_000_000.0, 0.0),
        (Airlock, {'size': 3.0}, 3.0, 300_000.0, 0.0),
        (Aerofins, {}, 20.0, 2_000_000.0, 0.0),
        (BreachingTube, {}, 3.0, 3_000_000.0, 0.0),
        (ForcedLinkageApparatus, {'tier': 'Basic'}, 2.0, 50_000.0, 0.0),
        (HolographicHull, {}, 0.0, 40_000_000.0, 200.0),
        (HotTub, {'users': 2}, 0.5, 6_000.0, 0.0),
        (ProbeDrones, {'count': 10}, 2.0, 1_000_000.0, 0.0),
        (AdvancedProbeDrones, {'count': 10}, 2.0, 1_600_000.0, 0.0),
        (RepairDrones, {}, 4.0, 800_000.0, 0.0),
        (MiningDrones, {'count': 10}, 20.0, 2_000_000.0, 0.0),
        (TrainingFacility, {'trainees': 2}, 4.0, 800_000.0, 0.0),
        (Brewery, {'litres_per_week': 20}, 1.0, 100_000.0, 0.0),
        (GourmetKitchen, {'diners': 4}, 4.0, 800_000.0, 0.0),
    ],
)
def test_converted_system_values_ignore_stale_numeric_inputs(
    part_cls, data, expected_tons, expected_cost, expected_power
):
    part = part_cls.model_validate({'tons': 99, 'cost': 99, 'power': 99, **data})
    part.bind(_dummy_owner_for(part))
    assert part.tons == pytest.approx(expected_tons)
    assert part.cost == pytest.approx(expected_cost)
    assert part.power == pytest.approx(expected_power)


@pytest.mark.parametrize(
    ('part_cls', 'data', 'expected_tons', 'expected_cost', 'expected_power'),
    [
        (CommonArea, {'tons': 2.0}, 2.0, 200_000.0, 0.0),
        (SwimmingPool, {'tons': 2.0}, 2.0, 40_000.0, 0.0),
        (Theatre, {'tons': 2.0}, 2.0, 200_000.0, 0.0),
        (Theatre, {'tons': 2.0, 'advanced': True}, 2.0, 400_000.0, 0.0),
        (ZeroGRoom, {'tons': 2.0}, 2.0, 50_000.0, 0.0),
        (CommercialZone, {'tons': 240.0}, 240.0, 48_000_000.0, 1.0),
        (Biosphere, {'tons': 4.0}, 4.0, 800_000.0, 4.0),
        (UNREPSystem, {'tons': 25.0}, 25.0, 12_500_000.0, 25.0),
    ],
)
def test_explicit_tonnage_system_values_are_property_backed_design_fields(
    part_cls, data, expected_tons, expected_cost, expected_power
):
    part = part_cls.model_validate({'cost': 99, 'power': 99, **data})
    part.bind(DummyOwner(15, 400))
    dump = part.model_dump()

    assert part.tons == pytest.approx(expected_tons)
    assert part.cost == pytest.approx(expected_cost)
    assert part.power == pytest.approx(expected_power)
    assert dump['tons'] == pytest.approx(expected_tons)
    assert 'cost' not in dump
    assert 'power' not in dump


def test_common_area_can_have_display_label():
    common_area = CommonArea(tons=8.0, display_label='Trophy Lounge')
    common_area.bind(DummyOwner(15, 400))

    assert common_area.notes.item_message == 'Trophy Lounge (Common Area)'


def test_common_area_display_label_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        habitation=HabitationSection(common_area=CommonArea(tons=8.0, display_label='Trophy Lounge')),
    )

    row = my_ship.build_spec().row('Trophy Lounge (Common Area)')

    assert row.tons == pytest.approx(8.0)


def test_holographic_hull_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[HolographicHull()]),
    )

    row = my_ship.build_spec().row('Holographic Hull')

    assert row.tons is None
    assert row.cost == pytest.approx(20_000_000.0)
    assert row.power == pytest.approx(-100.0)
    assert row.notes.infos == [
        'Can change hull colours, add graphics, and alter visual appearance without changing shape'
    ]


def test_breaching_tube_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[BreachingTube()]),
    )

    row = my_ship.build_spec().row('Breaching Tube')

    assert row.tons == pytest.approx(3.0)
    assert row.cost == pytest.approx(3_000_000.0)
    assert row.power is None
    assert row.notes.infos == [
        'DM +1 to Boarding Actions rolls',
        'Can only attach to disabled or otherwise inert ships',
        'Destroyed if either ship moves while attached; attached ship receives 2D damage',
    ]


@pytest.mark.parametrize(
    ('tier', 'tl', 'pilot_dm'),
    [
        ('Basic', 7, -2),
        ('Improved', 9, -1),
        ('Enhanced', 12, 0),
        ('Advanced', 15, 2),
    ],
)
def test_forced_linkage_apparatus_table_values(tier, tl, pilot_dm):
    apparatus = ForcedLinkageApparatus(tier=tier)
    apparatus.bind(DummyOwner(15, 400))

    assert apparatus.tl == tl
    assert apparatus.tons == pytest.approx(2.0)
    assert apparatus.pilot_check_dm == pilot_dm


def test_forced_linkage_apparatus_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[ForcedLinkageApparatus(tier='Enhanced')]),
    )

    row = my_ship.build_spec().row('Forced Linkage Apparatus (Enhanced)', section='Systems')

    assert row.tons == pytest.approx(2.0)
    assert row.cost == pytest.approx(100_000.0)
    assert row.power is None
    assert row.notes.infos == [
        'Pilot check DM +0',
        'Requires Thrust advantage of at least 1 over the target',
        'Cannot target ships above 5000 tons',
        'May be combined with a breaching tube',
    ]


def test_forced_linkage_apparatus_rejects_large_ship():
    apparatus = ForcedLinkageApparatus(tier='Enhanced')
    apparatus.bind(DummyOwner(12, 5_001))

    assert 'Forced linkage apparatus may only be used on ships of 5000 tons or less' in apparatus.notes.errors


def test_acceleration_bench_seats_four():
    bench = AccelerationBench()

    assert bench.seats == 4


def test_acceleration_bench_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[AccelerationBench()]),
    )

    row = my_ship.build_spec().row('Acceleration Bench')
    assert row.tons == pytest.approx(1.0)
    assert row.cost == pytest.approx(10_000.0)


def test_multi_environment_space_values_and_notes():
    space = MultiEnvironmentSpace(covered_tons=40)

    assert space.tons == pytest.approx(2.0)
    assert space.cost == pytest.approx(1_000_000.0)
    assert space.power == pytest.approx(2.0)
    assert space.notes.infos == [
        'Support equipment for modifying a designated area to unusual environmental conditions'
    ]


def test_multi_environment_space_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[MultiEnvironmentSpace(covered_tons=40)]),
    )

    row = my_ship.build_spec().row('Multi-Environment Space (40 tons)')
    assert row.tons == pytest.approx(2.0)
    assert row.cost == pytest.approx(1_000_000.0)
    assert row.power == pytest.approx(-2.0)


def test_vault_values_and_notes():
    vault = Vault(tons=8)

    assert vault.tons == pytest.approx(8.0)
    assert vault.cost == pytest.approx(4_000_000.0)
    assert vault.power == pytest.approx(0.0)
    assert vault.content_armour == 8
    assert vault.content_hull_points == 1
    assert vault.notes.infos == [
        'Vault armour and Hull points protect contents only, not the ship',
        'Contents can survive in vacuum for a limited time if the ship is destroyed',
    ]


def test_vault_armour_is_capped_at_10():
    vault = Vault(tons=40)

    assert vault.content_armour == 10
    assert vault.content_hull_points == 8


@pytest.mark.parametrize('tons', [3.99, 40.01])
def test_vault_reports_size_outside_allowed_range(tons):
    vault = Vault(tons=tons)

    assert 'Vault size must be between 4 and 40 tons' in vault.notes.errors


def test_vault_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[Vault(tons=8)]),
    )

    row = my_ship.build_spec().row('Vault')
    assert row.tons == pytest.approx(8.0)
    assert row.cost == pytest.approx(4_000_000.0)


@pytest.mark.parametrize(
    ('trap', 'expected_tl', 'expected_cost', 'expected_damage'),
    [
        (BoobyTrapTL6(), 6, 100_000.0, '3D'),
        (BoobyTrapTL8(), 8, 300_000.0, '5D'),
        (BoobyTrapTL10(), 10, 500_000.0, '6D'),
        (BoobyTrapTL12(), 12, 1_000_000.0, '8D'),
    ],
)
def test_booby_trap_values(trap, expected_tl, expected_cost, expected_damage):
    assert trap.tl == expected_tl
    assert trap.cost == pytest.approx(expected_cost)
    assert trap.damage_per_round == expected_damage


def test_booby_trapped_airlock_adds_cost_and_notes():
    airlock = Airlock(size=3, booby_trap=BoobyTrapTL8())
    airlock.bind(DummyOwner(12, 99))

    assert airlock.tons == pytest.approx(3.0)
    assert airlock.cost == pytest.approx(600_000.0)
    assert airlock.notes.infos == ['Booby-trapped: 5D damage/round']


def test_booby_trap_cost_applies_to_free_airlock():
    my_ship = ship.Ship(
        tl=12,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull, airlocks=[Airlock(booby_trap=BoobyTrapTL6())]),
    )

    airlock = my_ship.hull.airlocks[0]
    assert airlock.tons == pytest.approx(0.0)
    assert airlock.cost == pytest.approx(100_000.0)


def test_booby_trapped_airlock_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=99,
        hull=hull.Hull(configuration=hull.standard_hull, airlocks=[Airlock(booby_trap=BoobyTrapTL12())]),
    )

    row = my_ship.build_spec().row('Airlock (2 tons)')
    assert row.tons == pytest.approx(2.0)
    assert row.cost == pytest.approx(1_200_000.0)
    assert row.notes.infos == ['Booby-trapped: 8D damage/round']


def test_booby_trap_requires_matching_ship_tl():
    airlock = Airlock(booby_trap=BoobyTrapTL12())
    airlock.bind(DummyOwner(10, 99))

    assert 'Requires TL12, ship is TL10' in airlock.notes.errors


def test_construction_deck_values_and_notes():
    deck = ConstructionDeck(tons=100)
    deck.bind(DummyOwner(12, 400))

    assert deck.tons == pytest.approx(100.0)
    assert deck.cost == pytest.approx(50_000_000.0)
    assert deck.power == pytest.approx(100.0)
    assert deck.maximum_constructible_tons == pytest.approx(50.0)
    assert deck.notes.infos == ['Can build or repair ships up to 50 tons at TL12']


def test_construction_deck_appears_in_ship_spec():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[ConstructionDeck(tons=100)]),
    )

    row = my_ship.build_spec().row('Construction Deck')
    assert row.tons == pytest.approx(100.0)
    assert row.cost == pytest.approx(50_000_000.0)
    assert row.power == pytest.approx(-100.0)
    assert row.notes.infos == ['Can build or repair ships up to 50 tons at TL12']


def test_common_area_extras_notes_and_tl():
    brewery = Brewery(litres_per_week=20)
    kitchen = GourmetKitchen(diners=4)
    zero_g_room = ZeroGRoom(tons=2)

    brewery.bind(DummyOwner(9, 400))
    kitchen.bind(DummyOwner(12, 400))
    zero_g_room.bind(DummyOwner(12, 400))

    assert 'Requires TL10, ship is TL9' in brewery.notes.errors
    assert kitchen.notes.infos == [
        'Requires Steward 2 to use properly',
        'DM +1 when seeking high passengers',
    ]
    assert zero_g_room.notes.infos == ['Includes controls and safe-access portal']


@pytest.mark.parametrize(
    (
        'part',
        'expected_tl',
        'expected_capacity',
        'expected_protection',
        'expected_detection_dm',
        'expected_attack_dm',
    ),
    [
        (BasicReEntryCapsule(), 8, 1, None, None, None),
        (AssaultReEntryCapsule(), 10, 1, 20, -2, None),
        (HighSurvivabilityReEntryCapsule(), 14, 1, 30, -4, -2),
        (ReEntryPod(), 9, 2, None, None, None),
    ],
)
def test_re_entry_system_capabilities(
    part,
    expected_tl,
    expected_capacity,
    expected_protection,
    expected_detection_dm,
    expected_attack_dm,
):
    assert part.tl == expected_tl
    assert part.capacity == expected_capacity
    assert part.protection == expected_protection
    assert part.detection_dm == expected_detection_dm
    assert part.attack_dm == expected_attack_dm


def test_re_entry_capsule_notes():
    capsule = HighSurvivabilityReEntryCapsule()

    assert capsule.notes.infos == [
        'Emergency escape and planetary insertion system for one person',
        'Protection +30',
        'DM-4 to detect',
        'DM-2 against attacks',
    ]


def test_re_entry_pod_notes():
    pod = ReEntryPod()

    assert pod.notes.infos == [
        'Emergency escape and planetary insertion system for two people',
        'Includes gliding surface and computer guidance; Flyer (wing) can take manual control',
    ]


def test_re_entry_systems_appear_in_ship_spec():
    my_ship = ship.Ship(
        tl=14,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(
            internal_systems=[
                HighSurvivabilityReEntryCapsule(),
                ReEntryPod(),
            ]
        ),
    )

    spec = my_ship.build_spec()
    capsule_row = spec.row('Re-entry Capsule (high-survivability)')
    pod_row = spec.row('Re-entry Pod')
    assert capsule_row.tons == pytest.approx(0.5)
    assert capsule_row.cost == pytest.approx(100_000.0)
    assert pod_row.tons == pytest.approx(1.0)
    assert pod_row.cost == pytest.approx(150_000.0)


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


def test_unrep_system_transfer_rate_and_label():
    unrep = UNREPSystem(tons=25.0)
    unrep.bind(DummyOwner(12, 50_000))

    assert unrep.transfer_rate == pytest.approx(500.0)
    assert unrep.build_item() == 'UNREP System (500 tons/hour)'


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


def test_command_bridge_values_and_notes():
    command_bridge = CommandBridge()
    command_bridge.bind(DummyOwner(12, 6_000))

    assert command_bridge.tons == pytest.approx(40.0)
    assert command_bridge.cost == pytest.approx(30_000_000.0)
    assert command_bridge.power == pytest.approx(0.0)
    assert command_bridge.tactics_naval_dm == 1
    assert command_bridge.build_item() == 'Command Bridge'
    assert command_bridge.notes.infos == ['DM +1 to Tactics (naval) checks made within the command bridge']


def test_command_bridge_requires_more_than_5000_tons():
    command_bridge = CommandBridge()
    command_bridge.bind(DummyOwner(12, 5_000))

    assert command_bridge.notes.errors == ['Command bridge requires displacement greater than 5000 tons']


def test_command_bridge_is_separate_from_ship_control_bridge_in_spec():
    # Based on the Valiant light cruiser bridge rows in refs/hg/70_system_defence_boat.md.
    my_ship = ship.Ship(
        tl=15,
        displacement=30_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        command=CommandSection(bridge=Bridge(holographic=True)),
        systems=SystemsSection(internal_systems=[CommandBridge()]),
    )

    spec = my_ship.build_spec()
    bridge_row = spec.row('Holographic Controls', section='Command')
    command_bridge_row = spec.row('Command Bridge', section='Systems')

    assert bridge_row.tons == pytest.approx(60.0)
    assert bridge_row.cost == pytest.approx(187_500_000.0)
    assert command_bridge_row.tons == pytest.approx(40.0)
    assert command_bridge_row.cost == pytest.approx(30_000_000.0)
    assert command_bridge_row.notes.infos == ['DM +1 to Tactics (naval) checks made within the command bridge']


def test_grav_screen_values_scale_by_displacement():
    grav_screen = GravScreen()
    grav_screen.bind(DummyOwner(12, 401))

    assert grav_screen.tons == pytest.approx(3.0)
    assert grav_screen.cost == pytest.approx(3_000_000.0)
    assert grav_screen.power == pytest.approx(6.0)
    assert grav_screen.notes.infos == [
        'Blocks densitometers; the presence of a grav screen is obvious to sensor operators'
    ]


def test_gravity_well_generator_values_and_notes():
    generator = GravityWellGenerator()
    generator.bind(DummyOwner(16, 10_000))

    assert generator.tons == pytest.approx(100.0)
    assert generator.cost == pytest.approx(120_000_000.0)
    assert generator.power == pytest.approx(500.0)
    assert generator.build_item() == 'Gravity Well Generator'
    assert generator.notes.infos == ['Creates an artificial gravity well; tactical effects are out of scope']


def test_jump_filter_values_and_notes():
    jump_filter = JumpFilter()
    jump_filter.bind(DummyOwner(14, 10_000))

    assert jump_filter.tons == pytest.approx(0.0)
    assert jump_filter.cost == pytest.approx(5_000_000.0)
    assert jump_filter.power == pytest.approx(1.0)
    assert jump_filter.bandwidth == 5
    assert jump_filter.build_item() == 'Jump Filter'
    assert jump_filter.notes.infos == [
        'Analyses witnessed jumps to help predict destination; operational effects are out of scope'
    ]


def test_jump_filter_requires_tl14():
    jump_filter = JumpFilter()
    jump_filter.bind(DummyOwner(13, 10_000))

    assert jump_filter.notes.errors == ['Requires TL14, ship is TL13']


def test_jump_filter_spec_row():
    my_ship = ship.Ship(
        tl=14,
        displacement=10_000,
        hull=hull.Hull(configuration=hull.standard_hull),
        systems=SystemsSection(internal_systems=[JumpFilter()]),
    )

    row = my_ship.build_spec().row('Jump Filter', section='Systems')

    assert row.tons is None
    assert row.cost == pytest.approx(5_000_000.0)
    assert row.power == pytest.approx(-1.0)


@pytest.mark.parametrize(
    ('displacement', 'expected_note'),
    [
        (99, 'Psionic shielding makes ships under 100 tons impenetrable to Clairvoyance and Telepathy'),
        (100, 'DM-4 to Clairvoyance and Telepathy powers within or upon the ship'),
        (300, 'DM-4 to Clairvoyance and Telepathy powers within or upon the ship'),
        (301, 'DM-2 to Clairvoyance and Telepathy powers within or upon the ship'),
        (500, 'DM-2 to Clairvoyance and Telepathy powers within or upon the ship'),
        (501, 'No Clairvoyance or Telepathy DM for ships above 500 tons'),
    ],
)
def test_psionic_shielding_values_and_notes(displacement, expected_note):
    shielding = PsionicShielding()
    shielding.bind(DummyOwner(12, displacement))

    assert shielding.tons == pytest.approx(displacement * 0.01)
    assert shielding.cost == pytest.approx(shielding.tons * 500_000.0)
    assert shielding.power == pytest.approx(0.0)
    assert shielding.build_item() == 'Psionic Shielding'
    assert shielding.notes.infos == [expected_note]


def test_psionic_shielding_requires_tl12():
    shielding = PsionicShielding()
    shielding.bind(DummyOwner(11, 400))

    assert shielding.notes.errors == ['Requires TL12, ship is TL11']


@pytest.mark.parametrize(
    ('displacement', 'expected_cost'),
    [
        (1, 1_000_000.0),
        (100, 1_000_000.0),
        (101, 2_000_000.0),
        (400, 4_000_000.0),
    ],
)
def test_advanced_psionic_shielding_values_and_notes(displacement, expected_cost):
    shielding = AdvancedPsionicShielding()
    shielding.bind(DummyOwner(16, displacement))

    assert shielding.tons == pytest.approx(0.0)
    assert shielding.cost == pytest.approx(expected_cost)
    assert shielding.power == pytest.approx(0.0)
    assert shielding.build_item() == 'Advanced Psionic Shielding'
    assert shielding.notes.infos == ['Advanced psionic shielding consumes no tonnage']


def test_advanced_psionic_shielding_requires_tl16():
    shielding = AdvancedPsionicShielding()
    shielding.bind(DummyOwner(15, 400))

    assert shielding.notes.errors == ['Requires TL16, ship is TL15']


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
    assert 'tons' not in airlock.model_dump()
    assert 'cost' not in airlock.model_dump()
    assert 'power' not in airlock.model_dump()


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
            GravScreen(),
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
        GravScreen,
        Workshop,
        MedicalBay,
        TrainingFacility,
        ProbeDrones,
        RepairDrones,
    ]

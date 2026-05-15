import pytest

from ceres.make.robot.chassis import (
    RobotSize,
    Trait,
    base_armour,
    base_available_slots,
    base_endurance_multiplier,
    chassis_entry,
    size_trait,
)


class TestRobotSizeTable:
    def test_all_sizes_present(self):
        for size in RobotSize:
            entry = chassis_entry(size)
            assert entry.base_slots > 0
            assert entry.base_hits > 0
            assert entry.basic_cost > 0

    @pytest.mark.parametrize(
        'size, expected_slots, expected_hits, expected_dm, expected_cost',
        [
            (RobotSize.SIZE_1, 1, 1, -4, 100),
            (RobotSize.SIZE_2, 2, 4, -3, 200),
            (RobotSize.SIZE_3, 4, 8, -2, 400),
            (RobotSize.SIZE_4, 8, 12, -1, 800),
            (RobotSize.SIZE_5, 16, 20, 0, 1000),
            (RobotSize.SIZE_6, 32, 32, 1, 2000),
            (RobotSize.SIZE_7, 64, 50, 2, 4000),
            (RobotSize.SIZE_8, 128, 72, 3, 8000),
        ],
    )
    def test_chassis_row_values(self, size, expected_slots, expected_hits, expected_dm, expected_cost):
        entry = chassis_entry(size)
        assert entry.base_slots == expected_slots
        assert entry.base_hits == expected_hits
        assert entry.attack_dm == expected_dm
        assert entry.basic_cost == expected_cost

    def test_size_is_int_enum(self):
        assert RobotSize.SIZE_3 == 3
        assert RobotSize.SIZE_3 + 1 == RobotSize.SIZE_4


class TestBaseArmour:
    @pytest.mark.parametrize(
        'tl, expected',
        [
            (6, 2),
            (7, 2),
            (8, 2),
            (9, 3),
            (10, 3),
            (11, 3),
            (12, 4),
            (13, 4),
            (14, 4),
            (15, 4),
            (16, 4),
            (17, 4),
            (18, 5),
        ],
    )
    def test_armour_by_tl(self, tl, expected):
        assert base_armour(tl) == expected

    def test_domestic_servant_tl8(self):
        assert base_armour(8) == 2

    def test_basic_lab_control_tl12(self):
        assert base_armour(12) == 4

    def test_below_tl6_treated_as_tl6_band(self):
        # Rule text does not define a band below TL6; implementation falls back to 2
        assert base_armour(5) == 2
        assert base_armour(1) == 2


class TestEnduranceMultiplier:
    def test_below_tl12(self):
        assert base_endurance_multiplier(8) == 1.0
        assert base_endurance_multiplier(11) == 1.0

    def test_tl12_to_14(self):
        assert base_endurance_multiplier(12) == 1.5
        assert base_endurance_multiplier(14) == 1.5

    def test_tl15_plus(self):
        assert base_endurance_multiplier(15) == 2.0
        assert base_endurance_multiplier(17) == 2.0


class TestSizeTrait:
    @pytest.mark.parametrize(
        'size, expected_name, expected_value',
        [
            (RobotSize.SIZE_1, 'Small', -4),
            (RobotSize.SIZE_2, 'Small', -3),
            (RobotSize.SIZE_3, 'Small', -2),
            (RobotSize.SIZE_4, 'Small', -1),
            (RobotSize.SIZE_6, 'Large', 1),
            (RobotSize.SIZE_7, 'Large', 2),
            (RobotSize.SIZE_8, 'Large', 3),
        ],
    )
    def test_size_trait_values(self, size, expected_name, expected_value):
        trait = size_trait(size)
        assert trait is not None
        assert trait.name == expected_name
        assert trait.value == expected_value

    def test_size_5_no_trait(self):
        assert size_trait(RobotSize.SIZE_5) is None


class TestAvailableSlots:
    def test_normal_locomotion(self):
        assert base_available_slots(RobotSize.SIZE_1, none_locomotion=False) == 1
        assert base_available_slots(RobotSize.SIZE_3, none_locomotion=False) == 4
        assert base_available_slots(RobotSize.SIZE_5, none_locomotion=False) == 16

    def test_none_locomotion_adds_25_percent(self):
        # Size 1: ceil(1 * 1.25) = 2
        assert base_available_slots(RobotSize.SIZE_1, none_locomotion=True) == 2
        # Size 4: ceil(8 * 1.25) = 10
        assert base_available_slots(RobotSize.SIZE_4, none_locomotion=True) == 10
        # Size 5: ceil(16 * 1.25) = 20
        assert base_available_slots(RobotSize.SIZE_5, none_locomotion=True) == 20

    def test_basic_lab_control_size1_none(self):
        # refs: robot.hits==1, available_slots==2 (ceil(1*1.25))
        assert base_available_slots(RobotSize.SIZE_1, none_locomotion=True) == 2


class TestTrait:
    def test_trait_without_value(self):
        t = Trait('ATV')
        assert str(t) == 'ATV'

    def test_trait_with_int_value(self):
        t = Trait('Small', -2)
        assert str(t) == 'Small (-2)'

    def test_trait_with_str_value(self):
        t = Trait('Flyer', 'idle')
        assert str(t) == 'Flyer (idle)'

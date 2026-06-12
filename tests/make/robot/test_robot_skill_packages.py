"""Tests for robot skill package facade classes (bandwidth, cost, display)."""

from ceres.character.domain.characteristics import Chars
from ceres.make.robot.skills import Admin, Athletics, Electronics, Engineer, GunCombat


class TestBandwidth:
    def test_admin_level_0_is_0(self):
        assert Admin().bandwidth == 0

    def test_admin_level_1_is_1(self):
        assert Admin(level=1).bandwidth == 1

    def test_admin_level_2_is_2(self):
        assert Admin(level=2).bandwidth == 2

    def test_electronics_unspecialised_is_0(self):
        assert Electronics().bandwidth == 0

    def test_electronics_one_speciality_level_1_is_1(self):
        assert Electronics(comms=1).bandwidth == 1

    def test_electronics_two_specialities_level_1_is_2(self):
        assert Electronics(comms=1, computers=1).bandwidth == 2

    def test_electronics_four_specialities_level_1_is_4(self):
        assert Electronics(comms=1, computers=1, sensors=1, remote_ops=1).bandwidth == 4

    def test_electronics_one_speciality_level_2_is_2(self):
        assert Electronics(comms=2).bandwidth == 2

    def test_electronics_mixed_levels(self):
        # comms=2 → bw 2; computers=1 → bw 1; total 3
        assert Electronics(comms=2, computers=1).bandwidth == 3


class TestCost:
    def test_admin_level_0_is_100(self):
        assert Admin().cost == 100.0

    def test_admin_level_1_is_1000(self):
        assert Admin(level=1).cost == 1000.0

    def test_admin_level_2_is_10000(self):
        assert Admin(level=2).cost == 10000.0

    def test_electronics_unspecialised_is_100(self):
        assert Electronics().cost == 100.0

    def test_electronics_comms_level_1_is_1000(self):
        assert Electronics(comms=1).cost == 1000.0

    def test_electronics_two_specialities_level_1_is_2000(self):
        assert Electronics(comms=1, computers=1).cost == 2000.0

    def test_electronics_four_specialities_level_1_is_4000(self):
        assert Electronics(comms=1, computers=1, sensors=1, remote_ops=1).cost == 4000.0

    def test_engineer_four_specialities_level_1_is_8000(self):
        # Engineer base_cost=200, 4 specialities at level 1: 4 × 2000 = 8000
        assert Engineer(m_drive=1, j_drive=1, life_support=1, power=1).cost == 8000.0


class TestDisplay:
    def test_electronics_unspecialised_int_dm_2_shows_all_2(self):
        entries = Electronics().display_entries({Chars.INT: 2})
        # All 4 specialities at 0+2=2 → same level → "(All) 2"
        assert entries == {'Electronics (All)': 2}

    def test_electronics_all_level1_int_dm_2_shows_all_3(self):
        entries = Electronics(comms=1, computers=1, sensors=1, remote_ops=1).display_entries({Chars.INT: 2})
        assert entries == {'Electronics (All)': 3}

    def test_electronics_three_specialities_level1_int_dm_2(self):
        # comms=3, computers=3, sensors=3, remote_ops=0+2=2 → not all same → individual
        entries = Electronics(comms=1, computers=1, sensors=1).display_entries({Chars.INT: 2})
        assert entries.get('Electronics (Comms)') == 3
        assert entries.get('Electronics (Computers)') == 3
        assert entries.get('Electronics (Sensors)') == 3
        assert entries.get('Electronics (Remote Ops)') == 2

    def test_gun_combat_level0_dex_dm_0_shows_plain_0(self):
        entries = GunCombat().display_entries({Chars.DEX: 0})
        assert entries == {'Gun Combat': 0}

    def test_gun_combat_level0_dex_dm_2_shows_all_2(self):
        entries = GunCombat().display_entries({Chars.DEX: 2})
        assert entries == {'Gun Combat (All)': 2}

    def test_athletics_unspecialised_str2_dex0(self):
        # strength=0+2=2, dexterity=0+0=0, endurance=no char → not all same → show strength only
        entries = Athletics().display_entries({Chars.STR: 2, Chars.DEX: 0})
        assert entries.get('Athletics (Strength)') == 2
        assert 'Athletics (Dexterity)' not in entries

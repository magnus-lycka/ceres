"""Unit tests for characteristics.py — Chars enum and characteristic_dm."""

from ceres.character.domain.characteristics import UCP_STATS, Chars, ConnectionKind, characteristic_dm


class TestCharacteristicDm:
    def test_zero_returns_minus_3(self):
        assert characteristic_dm(0) == -3

    def test_negative_returns_minus_3(self):
        assert characteristic_dm(-1) == -3

    def test_3_returns_minus_1(self):
        assert characteristic_dm(3) == -1

    def test_6_returns_0(self):
        assert characteristic_dm(6) == 0

    def test_9_returns_1(self):
        assert characteristic_dm(9) == 1

    def test_12_returns_2(self):
        assert characteristic_dm(12) == 2

    def test_15_returns_3(self):
        assert characteristic_dm(15) == 3


class TestCharsEnum:
    def test_str_value(self):
        assert Chars.STR == 'STR'

    def test_psi_present(self):
        assert Chars.PSI in Chars

    def test_all_expected_values(self):
        expected = {'STR', 'DEX', 'END', 'INT', 'EDU', 'SOC', 'CHA', 'PSI'}
        assert {c.value for c in Chars} == expected


class TestConnectionKind:
    def test_contact_value(self):
        assert ConnectionKind.CONTACT == 'connection_contact'

    def test_all_four_kinds(self):
        assert set(ConnectionKind) == {
            ConnectionKind.CONTACT,
            ConnectionKind.ALLY,
            ConnectionKind.RIVAL,
            ConnectionKind.ENEMY,
        }


class TestUcpStats:
    def test_six_elements(self):
        assert len(UCP_STATS) == 6

    def test_order(self):
        assert UCP_STATS == (Chars.STR, Chars.DEX, Chars.END, Chars.INT, Chars.EDU, Chars.SOC)

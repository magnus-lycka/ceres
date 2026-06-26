import pytest

from ceres.shared import CeresPart, Equipment, ehex_to_int, int_to_ehex


class TestEhexToInt:
    def test_digits(self) -> None:
        assert [ehex_to_int(str(d)) for d in range(10)] == list(range(10))

    def test_a_through_h(self) -> None:
        assert ehex_to_int('A') == 10
        assert ehex_to_int('B') == 11
        assert ehex_to_int('F') == 15
        assert ehex_to_int('G') == 16
        assert ehex_to_int('H') == 17

    def test_j_skips_i(self) -> None:
        assert ehex_to_int('J') == 18

    def test_k_through_n(self) -> None:
        assert ehex_to_int('K') == 19
        assert ehex_to_int('N') == 22

    def test_p_skips_o(self) -> None:
        assert ehex_to_int('P') == 23

    def test_q_through_z(self) -> None:
        assert ehex_to_int('Q') == 24
        assert ehex_to_int('Z') == 33

    def test_lowercase_raises(self) -> None:
        with pytest.raises(ValueError):
            ehex_to_int('a')

    def test_i_raises(self) -> None:
        with pytest.raises(ValueError):
            ehex_to_int('I')

    def test_o_raises(self) -> None:
        with pytest.raises(ValueError):
            ehex_to_int('O')

    def test_invalid_char_raises(self) -> None:
        with pytest.raises(ValueError):
            ehex_to_int('!')


class TestIntToEhex:
    def test_digits(self) -> None:
        assert [int_to_ehex(d) for d in range(10)] == [str(d) for d in range(10)]

    def test_10_through_17(self) -> None:
        assert int_to_ehex(10) == 'A'
        assert int_to_ehex(15) == 'F'
        assert int_to_ehex(16) == 'G'
        assert int_to_ehex(17) == 'H'

    def test_18_is_j(self) -> None:
        assert int_to_ehex(18) == 'J'

    def test_19_through_22(self) -> None:
        assert int_to_ehex(19) == 'K'
        assert int_to_ehex(22) == 'N'

    def test_23_is_p(self) -> None:
        assert int_to_ehex(23) == 'P'

    def test_24_through_33(self) -> None:
        assert int_to_ehex(24) == 'Q'
        assert int_to_ehex(33) == 'Z'

    def test_negative_raises(self) -> None:
        with pytest.raises(ValueError):
            int_to_ehex(-1)

    def test_34_raises(self) -> None:
        with pytest.raises(ValueError):
            int_to_ehex(34)


class TestEhexRoundtrip:
    def test_all_values_roundtrip(self) -> None:
        for i in range(34):
            assert ehex_to_int(int_to_ehex(i)) == i


class TestEquipment:
    def test_empty_defaults(self):
        e = Equipment()
        assert e.tl == 0
        assert e.cost == 0.0
        assert e.mass_kg == 0.0
        assert e.parts == []

    def test_with_explicit_fields(self):
        part = CeresPart(tl=12, cost=1000.0)
        e = Equipment(parts=[part], tl=12, cost=1000.0, mass_kg=0.5)
        assert e.tl == 12
        assert e.cost == 1000.0
        assert e.mass_kg == 0.5
        assert e.parts == [part]

    def test_is_frozen(self):
        from pydantic import ValidationError

        e = Equipment()
        with pytest.raises(ValidationError):
            e.tl = 5

    def test_serialises_and_roundtrips(self):
        part = CeresPart(tl=10, cost=500.0)
        e = Equipment(parts=[part], tl=10, cost=500.0, mass_kg=0.25)
        json_str = e.model_dump_json()
        e2 = Equipment.model_validate_json(json_str)
        assert e2.tl == 10
        assert e2.cost == 500.0
        assert e2.mass_kg == 0.25
        assert e2.parts[0].tl == 10

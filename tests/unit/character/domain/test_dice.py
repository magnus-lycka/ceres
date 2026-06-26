"""Unit tests for DiceRoll."""

from pydantic import BaseModel
import pytest

from ceres.character.domain.dice import DiceRoll

# ── parse ─────────────────────────────────────────────────────────────────────


def test_parse_single_die_without_count():
    d = DiceRoll.parse('d6')
    assert d.count == 1
    assert d.faces == 6


def test_parse_single_die_with_explicit_one():
    d = DiceRoll.parse('1d6')
    assert d.count == 1
    assert d.faces == 6


def test_parse_multiple_dice():
    d = DiceRoll.parse('2d6')
    assert d.count == 2
    assert d.faces == 6


def test_parse_d3():
    d = DiceRoll.parse('d3')
    assert d.count == 1
    assert d.faces == 3


def test_parse_two_d3():
    d = DiceRoll.parse('2d3')
    assert d.count == 2
    assert d.faces == 3


def test_parse_is_case_insensitive():
    assert DiceRoll.parse('D6') == DiceRoll.parse('d6')
    assert DiceRoll.parse('2D6') == DiceRoll.parse('2d6')
    assert DiceRoll.parse('1D3') == DiceRoll.parse('1d3')


def test_parse_invalid_raises():
    with pytest.raises(ValueError):
        DiceRoll.parse('invalid')


def test_parse_no_d_raises_value_error():
    with pytest.raises(ValueError, match='Invalid dice notation'):
        DiceRoll.parse('2x6')


# ── roll_options ──────────────────────────────────────────────────────────────


def test_roll_options_d6():
    assert DiceRoll(count=1, faces=6).roll_options() == [1, 2, 3, 4, 5, 6]


def test_roll_options_d3():
    assert DiceRoll(count=1, faces=3).roll_options() == [1, 2, 3]


def test_roll_options_2d6():
    assert DiceRoll(count=2, faces=6).roll_options() == list(range(2, 13))


def test_roll_options_2d3():
    assert DiceRoll(count=2, faces=3).roll_options() == [2, 3, 4, 5, 6]


def test_roll_options_min_equals_count():
    d = DiceRoll(count=3, faces=4)
    assert d.roll_options()[0] == 3


def test_roll_options_max_equals_count_times_faces():
    d = DiceRoll(count=3, faces=4)
    assert d.roll_options()[-1] == 12


# ── __str__ ───────────────────────────────────────────────────────────────────


def test_str_single_die():
    assert str(DiceRoll(count=1, faces=6)) == 'D6'


def test_str_multiple_dice():
    assert str(DiceRoll(count=2, faces=6)) == '2D6'


def test_str_d3():
    assert str(DiceRoll(count=1, faces=3)) == 'D3'


# ── Pydantic integration ──────────────────────────────────────────────────────


def test_pydantic_field_accepts_string_via_model_validate():
    class Model(BaseModel):
        dice: DiceRoll

    m = Model.model_validate({'dice': '2d3'})
    assert m.dice == DiceRoll(count=2, faces=3)


def test_pydantic_field_accepts_dice_roll_object():
    class Model(BaseModel):
        dice: DiceRoll

    d = DiceRoll(count=1, faces=6)
    m = Model(dice=d)
    assert m.dice == d


def test_pydantic_round_trips_via_json():
    class Model(BaseModel):
        dice: DiceRoll

    original = Model(dice=DiceRoll.parse('2d6'))
    restored = Model.model_validate_json(original.model_dump_json())
    assert restored.dice == original.dice

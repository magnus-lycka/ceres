"""Tests for the Customisation grade hierarchy (Step 2)."""

import pytest

from ceres.make.ship.base import NoteList
from ceres.make.ship.parts import (
    Advanced,
    Budget,
    EarlyPrototype,
    EnergyEfficient,
    HighTechnology,
    IncreasedSize,
    Prototype,
    SizeReduction,
    VeryAdvanced,
)
from ceres.make.ship.weapons import VeryHighYield

# ---------------------------------------------------------------------------
# Valid constructions and note_text
# ---------------------------------------------------------------------------


def test_advanced_size_reduction_is_valid():
    c = Advanced(modifications=[SizeReduction])
    assert not NoteList(c.notes).errors


def test_advanced_note_text():
    assert Advanced(modifications=[SizeReduction]).note_text == 'Advanced: Size Reduction'


def test_high_technology_three_size_reductions_is_valid():
    c = HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction])
    assert not NoteList(c.notes).errors


def test_high_technology_three_size_reductions_note_text():
    assert (
        HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction]).note_text
        == 'High Technology: Size Reduction × 3'
    )


def test_high_technology_very_high_yield_and_energy_efficient_is_valid():
    # VeryHighYield.advantage=2, EnergyEfficient.advantage=1 → 3 total
    c = HighTechnology(modifications=[VeryHighYield, EnergyEfficient])
    assert not NoteList(c.notes).errors


def test_high_technology_very_high_yield_and_energy_efficient_note_text():
    assert (
        HighTechnology(modifications=[VeryHighYield, EnergyEfficient]).note_text
        == 'High Technology: Very High Yield, Energy Efficient'
    )


def test_very_advanced_very_high_yield_is_valid():
    # VeryHighYield.advantage=2 → 2 total
    c = VeryAdvanced(modifications=[VeryHighYield])
    assert not NoteList(c.notes).errors


def test_budget_increased_size_is_valid():
    c = Budget(modifications=[IncreasedSize])
    assert not NoteList(c.notes).errors


def test_budget_note_text():
    assert Budget(modifications=[IncreasedSize]).note_text == 'Budget: Increased Size'


def test_prototype_increased_size_is_valid():
    c = Prototype(modifications=[IncreasedSize])
    assert not NoteList(c.notes).errors


def test_early_prototype_two_increased_size_is_valid():
    c = EarlyPrototype(modifications=[IncreasedSize, IncreasedSize])
    assert not NoteList(c.notes).errors


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_advanced_two_size_reductions_has_error():
    c = Advanced(modifications=[SizeReduction, SizeReduction])
    assert NoteList(c.notes).errors


def test_budget_size_reduction_has_error():
    # Budget requires 0 advantages, 1 disadvantage — SizeReduction is an advantage
    c = Budget(modifications=[SizeReduction])
    assert NoteList(c.notes).errors


def test_high_technology_two_points_has_error():
    c = HighTechnology(modifications=[VeryHighYield])  # only 2 points, need 3
    assert NoteList(c.notes).errors


def test_very_advanced_three_points_has_error():
    c = VeryAdvanced(modifications=[SizeReduction, SizeReduction, SizeReduction])  # 3 points, need 2
    assert NoteList(c.notes).errors


# ---------------------------------------------------------------------------
# Grade multipliers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ('grade_cls', 'cost_mult', 'tons_mult', 'tl_delta'),
    [
        (EarlyPrototype, 11.0, 2.0, -2),
        (Prototype, 6.0, 1.0, -1),
        (Budget, 0.75, 1.0, 0),
        (Advanced, 1.10, 1.0, 1),
        (VeryAdvanced, 1.25, 1.0, 2),
        (HighTechnology, 1.50, 1.0, 3),
    ],
)
def test_grade_multipliers(grade_cls, cost_mult, tons_mult, tl_delta):
    assert grade_cls._cost_multiplier == pytest.approx(cost_mult)
    assert grade_cls._tons_multiplier == pytest.approx(tons_mult)
    assert grade_cls._tl_delta == tl_delta


# ---------------------------------------------------------------------------
# JSON roundtrip
# ---------------------------------------------------------------------------


def test_roundtrip_advanced():
    from ceres.make.ship.parts import Customisation

    original = Advanced(modifications=[SizeReduction])
    restored = Customisation.model_validate_json(original.model_dump_json())
    assert type(restored) is Advanced
    assert restored.note_text == original.note_text


def test_roundtrip_high_technology():
    from ceres.make.ship.parts import Customisation

    original = HighTechnology(modifications=[VeryHighYield, EnergyEfficient])
    restored = Customisation.model_validate_json(original.model_dump_json())
    assert type(restored) is HighTechnology
    assert restored.note_text == original.note_text


def test_roundtrip_budget():
    from ceres.make.ship.parts import Customisation

    original = Budget(modifications=[IncreasedSize])
    restored = Customisation.model_validate_json(original.model_dump_json())
    assert type(restored) is Budget

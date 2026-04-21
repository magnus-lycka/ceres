"""Tests for the Customisation grade hierarchy (Step 2)."""

import json

import pytest

from tycho.parts import (
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
from tycho.weapons import VeryHighYield


# ---------------------------------------------------------------------------
# Valid constructions and note_text
# ---------------------------------------------------------------------------


def test_advanced_size_reduction_is_valid():
    c = Advanced(SizeReduction)
    assert not any(n.category.value == 'error' for n in c.notes)


def test_advanced_note_text():
    assert Advanced(SizeReduction).note_text == 'Advanced: Size Reduction'


def test_high_technology_three_size_reductions_is_valid():
    c = HighTechnology(SizeReduction, SizeReduction, SizeReduction)
    assert not any(n.category.value == 'error' for n in c.notes)


def test_high_technology_three_size_reductions_note_text():
    assert HighTechnology(SizeReduction, SizeReduction, SizeReduction).note_text == 'High Technology: Size Reduction × 3'


def test_high_technology_very_high_yield_and_energy_efficient_is_valid():
    # VeryHighYield.advantage=2, EnergyEfficient.advantage=1 → 3 total
    c = HighTechnology(VeryHighYield, EnergyEfficient)
    assert not any(n.category.value == 'error' for n in c.notes)


def test_high_technology_very_high_yield_and_energy_efficient_note_text():
    assert HighTechnology(VeryHighYield, EnergyEfficient).note_text == 'High Technology: Very High Yield, Energy Efficient'


def test_very_advanced_very_high_yield_is_valid():
    # VeryHighYield.advantage=2 → 2 total
    c = VeryAdvanced(VeryHighYield)
    assert not any(n.category.value == 'error' for n in c.notes)


def test_budget_increased_size_is_valid():
    c = Budget(IncreasedSize)
    assert not any(n.category.value == 'error' for n in c.notes)


def test_budget_note_text():
    assert Budget(IncreasedSize).note_text == 'Budget: Increased Size'


def test_prototype_increased_size_is_valid():
    c = Prototype(IncreasedSize)
    assert not any(n.category.value == 'error' for n in c.notes)


def test_early_prototype_two_increased_size_is_valid():
    c = EarlyPrototype(IncreasedSize, IncreasedSize)
    assert not any(n.category.value == 'error' for n in c.notes)


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_advanced_two_size_reductions_has_error():
    c = Advanced(SizeReduction, SizeReduction)
    assert any(n.category.value == 'error' for n in c.notes)


def test_budget_size_reduction_has_error():
    # Budget requires 0 advantages, 1 disadvantage — SizeReduction is an advantage
    c = Budget(SizeReduction)
    assert any(n.category.value == 'error' for n in c.notes)


def test_high_technology_two_points_has_error():
    c = HighTechnology(VeryHighYield)  # only 2 points, need 3
    assert any(n.category.value == 'error' for n in c.notes)


def test_very_advanced_three_points_has_error():
    c = VeryAdvanced(SizeReduction, SizeReduction, SizeReduction)  # 3 points, need 2
    assert any(n.category.value == 'error' for n in c.notes)


# ---------------------------------------------------------------------------
# Grade multipliers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(('grade_cls', 'cost_mult', 'tons_mult', 'tl_delta'), [
    (EarlyPrototype, 11.0, 2.0, -2),
    (Prototype,       6.0, 1.0, -1),
    (Budget,          0.75, 1.0, 0),
    (Advanced,        1.10, 1.0, 1),
    (VeryAdvanced,    1.25, 1.0, 2),
    (HighTechnology,  1.50, 1.0, 3),
])
def test_grade_multipliers(grade_cls, cost_mult, tons_mult, tl_delta):
    assert grade_cls._cost_multiplier == pytest.approx(cost_mult)
    assert grade_cls._tons_multiplier == pytest.approx(tons_mult)
    assert grade_cls._tl_delta == tl_delta


# ---------------------------------------------------------------------------
# JSON roundtrip
# ---------------------------------------------------------------------------


def test_roundtrip_advanced():
    from tycho.parts import Customisation
    original = Advanced(SizeReduction)
    restored = Customisation.model_validate_json(original.model_dump_json())
    assert type(restored) is Advanced
    assert restored.note_text == original.note_text


def test_roundtrip_high_technology():
    from tycho.parts import Customisation
    original = HighTechnology(VeryHighYield, EnergyEfficient)
    restored = Customisation.model_validate_json(original.model_dump_json())
    assert type(restored) is HighTechnology
    assert restored.note_text == original.note_text


def test_roundtrip_budget():
    from tycho.parts import Customisation
    original = Budget(IncreasedSize)
    restored = Customisation.model_validate_json(original.model_dump_json())
    assert type(restored) is Budget

"""Approval snapshots for ship part customisation grade hierarchy.

The grade hierarchy (Advanced, VeryAdvanced, HighTechnology, Budget, EarlyPrototype, Prototype)
controls cost/tonnage multipliers, TL delta, and which modifications are allowed.
"""

import pytest

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
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def _grade_row(grade) -> dict:
    return {
        'note_text': grade.note_text,
        'cost_multiplier': grade.cost_multiplier,
        'tons_multiplier': grade.tons_multiplier,
        'tl_delta': grade.tl_delta,
        'errors': grade.notes.errors,
    }


@pytest.mark.approval
def test_grade_hierarchy(snapshot):
    """All grades with canonical modifications — note_text, multipliers, tl_delta, and validation errors."""
    snap = AnnotatedSnapshot(
        {
            'Advanced_SizeReduction': _grade_row(Advanced(modifications=[SizeReduction])),
            'VeryAdvanced_VeryHighYield': _grade_row(VeryAdvanced(modifications=[VeryHighYield])),
            'HighTechnology_SizeReduction_x3': _grade_row(
                HighTechnology(modifications=[SizeReduction, SizeReduction, SizeReduction])
            ),
            'HighTechnology_VHY_EnergyEfficient': _grade_row(
                HighTechnology(modifications=[VeryHighYield, EnergyEfficient])
            ),
            'Budget_IncreasedSize': _grade_row(Budget(modifications=[IncreasedSize])),
            'EarlyPrototype_IncreasedSize_x2': _grade_row(EarlyPrototype(modifications=[IncreasedSize, IncreasedSize])),
            'Prototype_IncreasedSize': _grade_row(Prototype(modifications=[IncreasedSize])),
            'Advanced_TwoReductions_error': _grade_row(Advanced(modifications=[SizeReduction, SizeReduction])),
            'Budget_SizeReduction_error': _grade_row(Budget(modifications=[SizeReduction])),
            'HighTechnology_TwoPoints_error': _grade_row(HighTechnology(modifications=[VeryHighYield, VeryHighYield])),
            'VeryAdvanced_ThreePoints_error': _grade_row(
                VeryAdvanced(modifications=[VeryHighYield, VeryHighYield, VeryHighYield])
            ),
        }
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

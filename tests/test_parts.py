from typing import ClassVar

from ceres import parts
from ceres.base import ShipBase
from ceres.hull import ArmouredBulkhead


class DummyShip(ShipBase):
    def __init__(self, tl=14, displacement=100):
        super().__init__(tl=tl, displacement=displacement)


class FixedPart(parts.ShipPart):
    minimum_tl: ClassVar[int] = 9


class HighTlPart(parts.ShipPart):
    minimum_tl: ClassVar[int] = 15


class CustomPart(parts.CustomisableShipPart):
    possible_customisations: ClassVar[tuple[parts.Customisation, ...]] = (
        parts.EnergyEfficient,
        parts.SizeReduction,
        parts.Budget,
        parts.IncreasedSize,
    )


def test_base_part():
    part = FixedPart.model_validate({'cost': 1, 'power': 3.14, 'tons': 4.44})
    owner = DummyShip()
    part.bind(owner)
    assert part.cost == 1
    assert part.minimum_tl == 9
    assert part.ship_tl == 14
    assert part.effective_tl == 14
    assert part.power == 3.14
    assert part.tons == 4.44
    assert part.compute_cost() == 1
    assert part.compute_power() == 3.14
    assert part.compute_tons() == 4.44


def test_part_rejects_ship_below_minimum_tl():
    part = HighTlPart.model_validate({'cost': 1, 'power': 0, 'tons': 0})
    part.bind(DummyShip(tl=14))
    assert [('error', 'Requires TL15, ship is TL14')] == [(note.category.value, note.message) for note in part.notes]


def test_part_owner_raises_before_bind():
    part = FixedPart.model_validate({})
    try:
        _ = part.owner
    except RuntimeError as exc:
        assert str(exc) == 'FixedPart not bound to a Ship'
    else:
        raise AssertionError('Expected RuntimeError')


def test_part_can_generate_armoured_bulkhead_from_own_values():
    part = FixedPart.model_validate({'tons': 30.0, 'armoured_bulkhead': True})
    part.bind(DummyShip())
    bulkhead = part.armoured_bulkhead_part
    assert isinstance(bulkhead, ArmouredBulkhead)
    assert bulkhead.tons == 3.0
    assert bulkhead.cost == 600_000
    assert bulkhead.protected_item == 'FixedPart'


def test_customisable_part_validates_grade_against_customisations():
    part = CustomPart(
        customisation_grade=parts.CustomisationGrade.HIGH_TECHNOLOGY,
        customisations=(parts.EnergyEfficient, parts.SizeReduction),
    )
    expected = (
        'error',
        'Customisations do not match HIGH_TECHNOLOGY: expected 3 advantage(s) and 0 disadvantage(s), got 2 and 0',
    )
    assert expected in [
        (note.category.value, note.message) for note in part.notes
    ]


def test_customisable_part_rejects_disallowed_customisation():
    part = CustomPart(
        customisation_grade=parts.CustomisationGrade.ADVANCED,
        customisations=(parts.LongRange,),
    )
    assert ('error', 'Customisation not allowed for CustomPart: Long Range') in [
        (note.category.value, note.message) for note in part.notes
    ]


def test_customisable_part_exposes_shared_multipliers():
    part = CustomPart(
        customisation_grade=parts.CustomisationGrade.HIGH_TECHNOLOGY,
        customisations=(parts.EnergyEfficient, parts.SizeReduction, parts.SizeReduction),
    )
    assert part.total_advantages == 3
    assert part.total_disadvantages == 0
    assert part.customisation_tl_delta == 3
    assert part.customisation_cost_multiplier == 1.5
    assert part.customisation_tons_multiplier == 0.8
    assert part.customisation_power_multiplier == 0.75


def test_customisable_part_notes_and_fuel_multiplier_are_aggregated():
    part = CustomPart(
        customisation_grade=parts.CustomisationGrade.ADVANCED,
        customisations=(parts.OrbitalRange,),
    )
    assert part.customisation_fuel_multiplier == 1.0
    assert [(note.category.value, note.message) for note in part.customisation_notes] == [
        ('info', 'Operational range increased to orbital distances'),
    ]


def test_customisable_part_requires_grade_when_customisations_present():
    part = CustomPart(customisations=(parts.SizeReduction,))
    assert ('error', 'Customisations require a customisation grade') in [
        (note.category.value, note.message) for note in part.notes
    ]


def test_grade_helpers_return_none_for_unknown_counts():
    assert parts.grade_for_advantages(4) is None
    assert parts.grade_for_disadvantages(3) is None

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


def test_part_rejects_ship_below_minimum_tl():
    part = HighTlPart.model_validate({'cost': 1, 'power': 0, 'tons': 0})
    part.bind(DummyShip(tl=14))
    assert [('error', 'Requires TL15, ship is TL14')] == [(note.category.value, note.message) for note in part.notes]


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

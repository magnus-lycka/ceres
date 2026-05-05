from typing import ClassVar

import pytest

from ceres.make.ship import parts
from ceres.make.ship.base import NoteList, ShipBase
from ceres.make.ship.drives import OrbitalRange
from ceres.make.ship.hull import ArmouredBulkhead


class DummyShip(ShipBase):
    def __init__(self, tl=14, displacement=100):
        super().__init__(tl=tl, displacement=displacement)


class FixedPart(parts.ShipPart):
    tl: int = 9


class HighTlPart(parts.ShipPart):
    tl: int = 15


class CustomPart(parts.CustomisableShipPart):
    allowed_modifications: ClassVar[frozenset[str]] = frozenset(
        {
            parts.EnergyEfficient.name,
            parts.SizeReduction.name,
            parts.IncreasedSize.name,
        }
    )


class Tl12CustomPart(CustomPart):
    tl: int = 12


def test_base_part():
    part = FixedPart.model_validate({'cost': 1, 'power': 3.14, 'tons': 4.44})
    owner = DummyShip()
    part.bind(owner)
    assert part.cost == 1
    assert part.tl == 9
    assert part.assembly_tl == 14
    assert part.power == 3.14
    assert part.tons == 4.44
    assert part.compute_cost() == 1
    assert part.compute_power() == 3.14
    assert part.compute_tons() == 4.44


def test_part_rejects_ship_below_tl():
    part = HighTlPart.model_validate({'cost': 1, 'power': 0, 'tons': 0})
    part.bind(DummyShip(tl=14))
    assert NoteList(part.notes).errors == ['Requires TL15, ship is TL14']


def test_part_assembly_raises_before_bind():
    part = FixedPart.model_validate({})
    try:
        _ = part.assembly
    except RuntimeError as exc:
        assert str(exc) == 'FixedPart not bound to an Assembly'
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


def test_customisable_part_build_notes_appends_customisation_note():
    part = CustomPart(
        customisation=parts.HighTechnology(
            modifications=[parts.EnergyEfficient, parts.SizeReduction, parts.SizeReduction]
        )
    )
    assert 'High Technology: Energy Efficient, Size Reduction × 2' in NoteList(part.notes).infos


def test_customisable_part_group_key_differs_for_different_customisations():
    part_a = CustomPart(customisation=parts.Advanced(modifications=[parts.SizeReduction]))
    part_b = CustomPart(customisation=parts.Budget(modifications=[parts.IncreasedSize]))
    assert part_a.group_key != part_b.group_key


def test_customisable_part_rejects_disallowed_customisation_on_bind():
    part = CustomPart(customisation=parts.Advanced(modifications=[OrbitalRange]))
    part.bind(DummyShip())
    assert 'Modification not allowed for CustomPart: Orbital Range' in NoteList(part.notes).errors


def test_customisable_part_without_customisation_behaves_like_ship_part():
    part = CustomPart.model_validate({'cost': 1, 'power': 2, 'tons': 3})
    part.bind(DummyShip())
    assert part.cost == 1
    assert part.power == 2
    assert part.tons == 3


def test_customisable_part_without_customisation_uses_part_tl():
    part = Tl12CustomPart()
    part.bind(DummyShip(tl=11))
    assert NoteList(part.notes).errors == ['Requires TL12, ship is TL11']


@pytest.mark.parametrize(
    ('customisation', 'ship_tl', 'expected'),
    [
        (
            parts.EarlyPrototype(modifications=[parts.IncreasedSize, parts.IncreasedSize]),
            9,
            'Requires TL10, ship is TL9',
        ),
        (parts.Prototype(modifications=[parts.IncreasedSize]), 10, 'Requires TL11, ship is TL10'),
        (parts.Budget(modifications=[parts.IncreasedSize]), 11, 'Requires TL12, ship is TL11'),
        (parts.Advanced(modifications=[parts.SizeReduction]), 12, 'Requires TL13, ship is TL12'),
        (
            parts.VeryAdvanced(modifications=[parts.SizeReduction, parts.SizeReduction]),
            13,
            'Requires TL14, ship is TL13',
        ),
        (
            parts.HighTechnology(modifications=[parts.SizeReduction, parts.SizeReduction, parts.SizeReduction]),
            14,
            'Requires TL15, ship is TL14',
        ),
    ],
)
def test_customisable_part_applies_customisation_tl_delta(customisation, ship_tl, expected):
    part = Tl12CustomPart(customisation=customisation)
    part.bind(DummyShip(tl=ship_tl))
    assert expected in NoteList(part.notes).errors


def test_prototype_warns_when_ship_tl_is_high_enough_without_it():
    part = Tl12CustomPart(customisation=parts.Prototype(modifications=[parts.IncreasedSize]))
    part.bind(DummyShip(tl=12))
    assert 'Prototype not required: ship TL12 exceeds required TL11' in NoteList(part.notes).warnings


def test_early_prototype_warns_when_prototype_would_suffice():
    part = Tl12CustomPart(customisation=parts.EarlyPrototype(modifications=[parts.IncreasedSize, parts.IncreasedSize]))
    part.bind(DummyShip(tl=11))
    assert 'Early Prototype not required: ship TL11 exceeds required TL10' in NoteList(part.notes).warnings

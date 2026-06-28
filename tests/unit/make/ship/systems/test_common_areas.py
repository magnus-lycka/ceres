"""Unit tests for systems/common_areas.py — CommonArea, Theatre, Brewery, GourmetKitchen, etc."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.common_areas import (
    Brewery,
    CommonArea,
    GourmetKitchen,
    MultiEnvironmentSpace,
    Theatre,
    ZeroGRoom,
)


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=400):
    part.bind(_Ship(tl, displacement))
    return part


class TestCommonArea:
    def test_cost_per_ton(self):
        area = _bind(CommonArea(tons=2.0))
        assert area.cost == pytest.approx(200_000.0)

    def test_display_label_appears_in_item_message(self):
        area = _bind(CommonArea(tons=8.0, display_label='Trophy Lounge'))
        assert area.notes.item_message == 'Trophy Lounge (Common Area)'

    def test_no_display_label_gives_default_item(self):
        area = _bind(CommonArea(tons=2.0))
        assert area.notes.item_message == 'Common Area'

    def test_tons_is_a_serialized_design_field(self):
        area = CommonArea.model_validate({'cost': 999, 'power': 999, 'tons': 4.0})
        assert area.tons == 4.0
        dump = area.model_dump()
        assert dump['tons'] == 4.0
        assert 'cost' not in dump
        assert 'power' not in dump


class TestTheatre:
    def test_standard_cost(self):
        theatre = _bind(Theatre(tons=2.0))
        assert theatre.cost == pytest.approx(200_000.0)

    def test_advanced_doubles_cost(self):
        theatre = _bind(Theatre(tons=2.0, advanced=True))
        assert theatre.cost == pytest.approx(400_000.0)


class TestBrewery:
    def test_tl_below_10_is_an_error(self):
        brewery = _bind(Brewery(litres_per_week=20), tl=9)
        assert 'Requires TL10, ship is TL9' in brewery.notes.errors

    def test_tl10_has_no_error(self):
        brewery = _bind(Brewery(litres_per_week=20), tl=10)
        assert 'Requires TL10' not in '\n'.join(brewery.notes.errors)


class TestGourmetKitchen:
    def test_notes_include_steward_and_passenger_dm(self):
        kitchen = _bind(GourmetKitchen(diners=4))
        assert 'Requires Steward 2 to use properly' in kitchen.notes.infos
        assert 'DM +1 when seeking high passengers' in kitchen.notes.infos


class TestZeroGRoom:
    def test_notes_include_controls(self):
        room = _bind(ZeroGRoom(tons=2.0))
        assert 'Includes controls and safe-access portal' in room.notes.infos


class TestMultiEnvironmentSpace:
    def test_tons_is_5pct_of_covered_area(self):
        space = MultiEnvironmentSpace(covered_tons=40)
        assert space.tons == pytest.approx(2.0)

    def test_cost_is_25k_per_covered_ton(self):
        space = MultiEnvironmentSpace(covered_tons=40)
        assert space.cost == pytest.approx(1_000_000.0)

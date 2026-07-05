"""Unit tests for systems/common_areas.py — CommonArea, Theatre, Brewery, GourmetKitchen, etc."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.common_areas import (
    Brewery,
    CommercialZone,
    CommonArea,
    GourmetKitchen,
    HotTub,
    MultiEnvironmentSpace,
    SwimmingPool,
    Theatre,
    WetBar,
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
        assert area.power == 0.0

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


class TestCommercialZone:
    def test_cost_and_minimum_power(self):
        zone = _bind(CommercialZone(tons=50.0))
        assert zone.cost == 10_000_000.0
        assert zone.power == 1.0

    def test_power_scales_by_200_ton_blocks(self):
        zone = _bind(CommercialZone(tons=600.0))
        assert zone.power == 3.0


class TestSwimmingPool:
    def test_cost_is_20k_per_ton(self):
        pool = _bind(SwimmingPool(tons=5.0))
        assert pool.cost == 100_000.0
        assert pool.power == 0.0


class TestTheatre:
    def test_standard_cost(self):
        theatre = _bind(Theatre(tons=2.0))
        assert theatre.cost == pytest.approx(200_000.0)

    def test_advanced_doubles_cost(self):
        theatre = _bind(Theatre(tons=2.0, advanced=True))
        assert theatre.cost == pytest.approx(400_000.0)


class TestBrewery:
    def test_capacity_drives_tons_cost_and_description(self):
        brewery = _bind(Brewery(litres_per_week=40))
        assert brewery.item_description() == 'Brewery (40 litres/week)'
        assert brewery.tons == 2.0
        assert brewery.cost == 200_000.0
        assert brewery.power == 0.0

    def test_tl_below_10_is_an_error(self):
        brewery = _bind(Brewery(litres_per_week=20), tl=9)
        assert 'Requires TL10, ship is TL9' in brewery.notes.errors

    def test_tl10_has_no_error(self):
        brewery = _bind(Brewery(litres_per_week=20), tl=10)
        assert 'Requires TL10' not in '\n'.join(brewery.notes.errors)


class TestGourmetKitchen:
    def test_capacity_drives_tons_cost_power_and_singular_label(self):
        kitchen = _bind(GourmetKitchen(diners=1))
        assert kitchen.item_description() == 'Gourmet Kitchen (1 diner)'
        assert kitchen.tons == 1.0
        assert kitchen.cost == 200_000.0
        assert kitchen.power == 0.0

    def test_plural_label(self):
        kitchen = _bind(GourmetKitchen(diners=4))
        assert kitchen.item_description() == 'Gourmet Kitchen (4 diners)'

    def test_notes_include_steward_and_passenger_dm(self):
        kitchen = _bind(GourmetKitchen(diners=4))
        assert 'Requires Steward 2 to use properly' in kitchen.notes.infos
        assert 'DM +1 when seeking high passengers' in kitchen.notes.infos


class TestZeroGRoom:
    def test_fixed_cost_and_common_area_power(self):
        room = _bind(ZeroGRoom(tons=2.0))
        assert room.cost == 50_000.0
        assert room.power == 0.0

    def test_notes_include_controls(self):
        room = _bind(ZeroGRoom(tons=2.0))
        assert 'Includes controls and safe-access portal' in room.notes.infos


class TestMultiEnvironmentSpace:
    def test_tons_is_5pct_of_covered_area(self):
        space = MultiEnvironmentSpace(covered_tons=40)
        assert space.item_description() == 'Multi-Environment Space (40 tons)'
        assert space.tons == pytest.approx(2.0)

    def test_cost_is_25k_per_covered_ton(self):
        space = _bind(MultiEnvironmentSpace(covered_tons=40))
        assert space.cost == pytest.approx(1_000_000.0)
        assert space.power == 2.0
        assert any('unusual environmental conditions' in info for info in space.notes.infos)


class TestWetBar:
    def test_zero_tons_low_fixed_cost(self):
        bar = _bind(WetBar())
        assert bar.tons == 0.0
        assert bar.cost == 2_000.0
        assert bar.power == 0.0


class TestHotTub:
    def test_one_user_label_and_values(self):
        tub = _bind(HotTub(users=1))
        assert tub.item_description() == 'Hot Tub (1 User)'
        assert tub.tons == 0.25
        assert tub.cost == 3_000.0
        assert tub.power == 0.0

    def test_plural_user_label_and_values(self):
        tub = _bind(HotTub(users=4))
        assert tub.item_description() == 'Hot Tub (4 Users)'
        assert tub.tons == 1.0
        assert tub.cost == 12_000.0

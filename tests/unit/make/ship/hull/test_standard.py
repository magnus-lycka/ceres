"""Unit tests for hull configuration computed properties."""

from ceres.make.ship import hull
from ceres.make.ship.base import ShipBase
from ceres.make.ship.ship import Ship


class _Ship(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


class TestMassiveShipHullPoints:
    def test_large_ship_bracing_scale_starts_at_25000_tons(self):
        assert hull.standard_hull.points(24_999) == 9_999
        assert hull.standard_hull.points(25_000) == 12_500

    def test_capital_ship_bracing_scale_starts_at_100000_tons(self):
        assert hull.standard_hull.points(99_999) == 49_999
        assert hull.standard_hull.points(100_000) == 66_666

    def test_reinforced_modifier_preserved_at_large_scale(self):
        assert hull.standard_hull.model_copy(update={'reinforced': True}).points(25_000) == 13_750

    def test_light_modifier_preserved_at_capital_scale(self):
        assert hull.standard_hull.model_copy(update={'light': True}).points(100_000) == 60_000


class TestArmouredBulkheadSerialization:
    def test_computed_properties_not_in_dump(self):
        bulkhead = hull.ArmouredBulkhead.model_validate(
            {'protected_tonnage': 30.0, 'protected_item': 'M-Drive', 'tons': 999, 'cost': 999, 'power': 999}
        )
        bulkhead.bind(_Ship(12, 100))
        dump = bulkhead.model_dump()
        assert bulkhead.tons == 3.0
        assert bulkhead.cost == 600_000
        assert bulkhead.power == 0.0
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestStealthSerialization:
    def test_computed_properties_not_in_dump(self):
        stealth = hull.BasicStealth.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        stealth.bind(_Ship(12, 100))
        dump = stealth.model_dump()
        assert stealth.tons == 2.0
        assert stealth.cost == 4_000_000
        assert stealth.power == 0.0
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestHullValidation:
    def test_hull_cannot_be_both_reinforced_and_light(self):
        my_ship = Ship(
            tl=12,
            displacement=100,
            hull=hull.Hull(configuration=hull.standard_hull.model_copy(update={'reinforced': True, 'light': True})),
        )
        assert 'Hull cannot be both reinforced and light' in my_ship.notes.errors

    def test_military_hull_requires_capital_ship_displacement(self):
        my_ship = Ship(
            tl=14,
            displacement=5_000,
            hull=hull.Hull(configuration=hull.standard_hull.model_copy(update={'military': True})),
        )
        assert 'Military hull requires capital ship displacement: 5,000 <= 5,000 tons' in my_ship.notes.errors

    def test_military_hull_allowed_above_five_thousand_tons(self):
        my_ship = Ship(
            tl=14,
            displacement=5_001,
            hull=hull.Hull(configuration=hull.standard_hull.model_copy(update={'military': True})),
        )
        assert 'Military hull requires capital ship displacement' not in '\n'.join(my_ship.notes.errors)

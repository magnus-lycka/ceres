"""Unit tests for systems/logistics.py — UNREPSystem."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.logistics import UNREPSystem


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


class TestUNREPSystem:
    def test_item_description_includes_transfer_rate(self):
        assert UNREPSystem(tons=2.5).item_description() == 'UNREP System (50 tons/hour)'

    def test_transfer_rate_is_twenty_times_tonnage(self):
        assert UNREPSystem(tons=2.5).transfer_rate == pytest.approx(50.0)

    def test_power_equals_tonnage(self):
        system = UNREPSystem(tons=25.0)
        system.bind(_Ship())
        assert system.power == pytest.approx(25.0)

    def test_cost_per_ton(self):
        system = UNREPSystem(tons=25.0)
        system.bind(_Ship())
        assert system.cost == pytest.approx(12_500_000.0)

    def test_tons_is_serialized_design_field(self):
        system = UNREPSystem.model_validate({'tons': 25.0, 'cost': 999, 'power': 999})
        dump = system.model_dump()
        assert dump['tons'] == 25.0
        assert 'cost' not in dump
        assert 'power' not in dump

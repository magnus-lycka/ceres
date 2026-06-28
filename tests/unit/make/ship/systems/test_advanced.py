"""Unit tests for systems/advanced.py — GravScreen, GravityWellGenerator, JumpFilter."""

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.advanced import GravityWellGenerator, GravScreen, JumpFilter


class _Ship(ShipBase):
    def __init__(self, tl=15, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=15, displacement=400):
    part.bind(_Ship(tl, displacement))
    return part


class TestGravScreen:
    def test_computed_not_serialized(self):
        part = GravScreen.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        _bind(part)
        assert part.tons == 2.0
        assert part.cost == 2_000_000.0
        assert part.power == 4.0
        dump = part.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestGravityWellGenerator:
    def test_values(self):
        part = _bind(GravityWellGenerator())
        assert part.tons == 100.0
        assert part.cost == 120_000_000.0
        assert part.power == 500.0


class TestJumpFilter:
    def test_zero_tons_but_costs_power(self):
        part = _bind(JumpFilter())
        assert part.tons == 0.0
        assert part.cost == 5_000_000.0
        assert part.power == 1.0

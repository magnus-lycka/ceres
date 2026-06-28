"""Unit tests for systems/drones.py — ProbeDrones, AdvancedProbeDrones, RepairDrones, MiningDrones."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.drones import (
    AdvancedProbeDrones,
    MiningDrones,
    ProbeDrones,
    RepairDrones,
)


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=400):
    part.bind(_Ship(tl, displacement))
    return part


class TestProbeDrones:
    def test_tons_per_drone(self):
        assert _bind(ProbeDrones(count=10)).tons == pytest.approx(2.0)

    def test_cost_per_drone(self):
        assert _bind(ProbeDrones(count=10)).cost == pytest.approx(1_000_000.0)

    def test_computed_not_serialized(self):
        part = ProbeDrones.model_validate({'count': 10, 'tons': 999, 'cost': 999, 'power': 999})
        _bind(part)
        dump = part.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestAdvancedProbeDrones:
    def test_higher_cost_than_probe_drones(self):
        basic = _bind(ProbeDrones(count=10))
        advanced = _bind(AdvancedProbeDrones(count=10))
        assert advanced.cost > basic.cost
        assert advanced.tons == basic.tons


class TestRepairDrones:
    def test_four_tons_800k(self):
        part = _bind(RepairDrones())
        assert part.tons == 4.0
        assert part.cost == 800_000.0


class TestMiningDrones:
    def test_two_tons_per_drone(self):
        assert _bind(MiningDrones(count=10)).tons == pytest.approx(20.0)

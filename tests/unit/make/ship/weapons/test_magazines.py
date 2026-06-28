"""Unit tests for weapons/magazines.py — MissileStorage, TorpedoStorage, SandcasterCanisterStorage."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.weapons.magazines import MissileStorage, SandcasterCanisterStorage, TorpedoStorage


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=400):
    part.bind(_Ship(tl, displacement))
    return part


class TestTorpedoStorage:
    def test_three_torpedoes_per_ton(self):
        storage = TorpedoStorage(count=7_200)
        assert storage.tons == pytest.approx(2_400.0)

    def test_zero_cost(self):
        storage = TorpedoStorage(count=24)
        assert storage.cost == 0.0

    def test_build_item_includes_count(self):
        assert TorpedoStorage(count=7_200).build_item() == 'Torpedo Storage (7200)'

    def test_computed_not_serialized(self):
        storage = TorpedoStorage.model_validate({'count': 24, 'tons': 999, 'cost': 999, 'power': 999})
        dump = storage.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestMissileStorage:
    def test_twelve_missiles_per_ton(self):
        storage = _bind(MissileStorage(count=24))
        assert storage.tons == pytest.approx(2.0)

    def test_armoured_bulkhead_generates_child_part(self):
        storage = _bind(MissileStorage(count=480, armoured_bulkhead=True))
        assert storage.armoured_bulkhead_part is not None
        assert storage.armoured_bulkhead_part.tons == pytest.approx(4.0)
        assert storage.armoured_bulkhead_part.cost == pytest.approx(800_000.0)

    def test_no_armoured_bulkhead_part_without_flag(self):
        storage = _bind(MissileStorage(count=24))
        assert storage.armoured_bulkhead_part is None


class TestSandcasterCanisterStorage:
    def test_twenty_canisters_per_ton(self):
        storage = _bind(SandcasterCanisterStorage(count=20))
        assert storage.tons == pytest.approx(1.0)

    def test_zero_cost(self):
        storage = _bind(SandcasterCanisterStorage(count=20))
        assert storage.cost == 0.0

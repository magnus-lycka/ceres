"""Unit tests for weapons/point_defense.py — PD batteries and TorpedoInterceptorCluster."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.weapons.point_defense import (
    LaserPointDefenseBattery2,
    TorpedoInterceptorCluster,
)


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=1_000):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=1_000):
    part.bind(_Ship(tl, displacement))
    return part


class TestLaserPointDefenseBattery:
    def test_20_tons_10_mcr_20_power(self):
        battery = _bind(LaserPointDefenseBattery2())
        assert battery.tons == 20.0
        assert battery.cost == 10_000_000.0
        assert battery.power == 20.0

    def test_uses_one_hardpoint(self):
        battery = _bind(LaserPointDefenseBattery2())
        assert battery.hardpoints_required == 1

    def test_computed_not_serialized(self):
        battery = LaserPointDefenseBattery2.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        _bind(battery)
        dump = battery.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestTorpedoInterceptorCluster:
    def test_one_ton_one_mcr_one_power(self):
        cluster = _bind(TorpedoInterceptorCluster(), tl=10)
        assert cluster.tons == pytest.approx(1.0)
        assert cluster.cost == pytest.approx(1_000_000.0)
        assert cluster.power == pytest.approx(1.0)

    def test_one_shot_note_present(self):
        cluster = _bind(TorpedoInterceptorCluster(), tl=10)
        assert 'One-shot system; must be replaced dockside after firing' in cluster.notes.infos

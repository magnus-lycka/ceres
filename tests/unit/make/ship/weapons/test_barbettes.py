"""Unit tests for weapons/barbettes.py — barbette computed properties and item names."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.parts import VeryAdvanced
from ceres.make.ship.weapons.barbettes import (
    ParticleBarbette,
    PulseLaserBarbette,
    TorpedoBarbette,
)
from ceres.make.ship.weapons.common import VeryHighYield


class _Ship(ShipBase):
    def __init__(self, tl=13, displacement=400):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=13, displacement=400):
    part.bind(_Ship(tl, displacement))
    return part


class TestParticleBarbette:
    def test_five_tons_eight_mcr(self):
        barbette = _bind(ParticleBarbette())
        assert barbette.tons == pytest.approx(5.0)
        assert barbette.cost == pytest.approx(8_000_000.0)

    def test_item_includes_damage_multiple(self):
        assert 'Damage × 3 after armour' in _bind(ParticleBarbette()).build_item()

    def test_very_high_yield_increases_cost(self):
        base = _bind(ParticleBarbette())
        vhy = _bind(ParticleBarbette(customisation=VeryAdvanced(modifications=[VeryHighYield])))
        assert vhy.cost > base.cost

    def test_computed_not_serialized(self):
        barbette = ParticleBarbette.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        _bind(barbette)
        dump = barbette.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestTorpedoBarbette:
    def test_item_has_no_damage_multiple(self):
        barbette = _bind(TorpedoBarbette(), displacement=400)
        assert 'Damage' not in barbette.build_item()

    def test_crew_requirements(self):
        barbette = _bind(TorpedoBarbette(), displacement=400)
        assert barbette.crew_required_commercial == 1
        assert barbette.crew_required_military == 2


class TestPulseLaserBarbette:
    def test_five_tons_six_mcr_twelve_power(self):
        barbette = _bind(PulseLaserBarbette(), tl=12)
        assert barbette.tons == 5.0
        assert barbette.cost == 6_000_000.0
        assert barbette.power == 12.0

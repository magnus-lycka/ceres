"""Unit tests for systems/external.py — external fittings."""

from ceres.make.ship.base import ShipBase
from ceres.make.ship.systems.external import Aerofins, GrapplingArm, HolographicHull, TowCable


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=200):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=400):
    part.bind(_Ship(tl, displacement))
    return part


class TestAerofins:
    def test_five_percent_of_displacement(self):
        fins_200 = _bind(Aerofins(), displacement=200)
        fins_400 = _bind(Aerofins(), displacement=400)
        assert fins_200.tons == 10.0
        assert fins_400.tons == 20.0

    def test_cost_is_100k_per_ton(self):
        fins = _bind(Aerofins())
        assert fins.cost == 2_000_000.0
        assert fins.power == 0.0

    def test_pilot_dm_and_note_describe_atmospheric_benefit(self):
        fins = _bind(Aerofins())
        assert fins.atmospheric_pilot_dm == 2
        assert 'DM +2 to Pilot checks in atmosphere' in fins.notes.infos


class TestHolographicHull:
    def test_scales_with_displacement(self):
        hull = _bind(HolographicHull())
        assert hull.tons == 0.0
        assert hull.cost == 40_000_000.0
        assert hull.power == 200.0

    def test_computed_not_serialized(self):
        part = HolographicHull.model_validate({'tons': 999, 'cost': 999, 'power': 999})
        _bind(part)
        dump = part.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump

    def test_note_describes_visual_capability(self):
        hull = _bind(HolographicHull())
        assert any('hull colours' in info or 'visual appearance' in info for info in hull.notes.infos)


class TestTowCable:
    def test_one_percent_of_displacement(self):
        cable = _bind(TowCable(), displacement=400)
        assert cable.tons == 4.0
        assert cable.cost == 20_000.0
        assert cable.power == 0.0


class TestGrapplingArm:
    def test_fixed_two_ton_one_mcredit_installation(self):
        arm = _bind(GrapplingArm())
        assert arm.tons == 2.0
        assert arm.cost == 1_000_000.0
        assert arm.power == 0.0

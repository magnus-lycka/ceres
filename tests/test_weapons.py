import pytest

from ceres.base import ShipBase
from ceres.weapons import FixedFirmpoint, PulseLaser


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


# --- PulseLaser ---


def test_pulse_laser_base_cost():
    w = PulseLaser()
    assert w.base_cost == 1_000_000


def test_pulse_laser_base_power():
    w = PulseLaser()
    assert w.base_power == 4


def test_pulse_laser_no_upgrades_cost_modifier():
    w = PulseLaser()
    assert w.cost_modifier == pytest.approx(1.0)


def test_pulse_laser_energy_efficient_cost_modifier():
    # Advanced: 1 advantage, +10% cost
    w = PulseLaser(energy_efficient=True)
    assert w.cost_modifier == pytest.approx(1.10)


def test_pulse_laser_very_high_yield_cost_modifier():
    # Very Advanced: 2 advantages, +25% cost
    w = PulseLaser(very_high_yield=True)
    assert w.cost_modifier == pytest.approx(1.25)


def test_pulse_laser_high_technology_cost_modifier():
    # High Technology: 3 advantages (very_high_yield=2 + energy_efficient=1), +50% cost
    w = PulseLaser(very_high_yield=True, energy_efficient=True)
    assert w.cost_modifier == pytest.approx(1.50)


# --- FixedFirmpoint ---


def test_fixed_firmpoint_base_cost():
    fp = FixedFirmpoint(weapon=PulseLaser())
    fp.bind(DummyOwner(12, 6))
    # mount MCr0.1 + weapon MCr1 * 1.0 = 1,100,000
    assert float(fp.cost) == pytest.approx(1_100_000)


def test_fixed_firmpoint_high_technology_cost():
    fp = FixedFirmpoint(weapon=PulseLaser(very_high_yield=True, energy_efficient=True))
    fp.bind(DummyOwner(12, 6))
    # mount 100,000 + weapon 1,000,000 * 1.5 = 1,600,000
    assert float(fp.cost) == pytest.approx(1_600_000)


def test_fixed_firmpoint_tons_zero():
    fp = FixedFirmpoint(weapon=PulseLaser())
    fp.bind(DummyOwner(12, 6))
    assert float(fp.tons) == 0


def test_fixed_firmpoint_base_power():
    # Firmpoint reduces by 25%: floor(4 * 0.75) = 3
    fp = FixedFirmpoint(weapon=PulseLaser())
    fp.bind(DummyOwner(12, 6))
    assert float(fp.power) == 3


def test_fixed_firmpoint_energy_efficient_power():
    # Firmpoint -25% * energy_efficient -25%: floor(4 * 0.75 * 0.75) = floor(2.25) = 2
    fp = FixedFirmpoint(weapon=PulseLaser(very_high_yield=True, energy_efficient=True))
    fp.bind(DummyOwner(12, 6))
    assert float(fp.power) == 2


def test_fixed_firmpoint_recomputes_cost_from_input():
    fp = FixedFirmpoint.model_validate({'weapon': {}, 'cost': 999})
    fp.bind(DummyOwner(12, 6))
    assert fp.cost == pytest.approx(1_100_000)


def test_fixed_firmpoint_recomputes_tons_from_input():
    fp = FixedFirmpoint.model_validate({'weapon': {}, 'tons': 999})
    fp.bind(DummyOwner(12, 6))
    assert fp.tons == 0

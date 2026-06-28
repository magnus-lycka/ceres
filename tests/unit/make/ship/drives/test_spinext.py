"""Unit tests for drives/spinext.py — SpinExtPlasmaDrive computed properties and modifications."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.drives.spinext import (
    SpinExtPlasmaDrive,
    SpinExtPlasmaDriveEnergyEfficient,
    SpinExtPlasmaDriveFuelEfficient,
    SpinExtPlasmaDriveSizeReduction,
)


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=100):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=100):
    part.bind(_Ship(tl, displacement))
    return part


class TestSpinExtPlasmaDriveValues:
    def test_tons_is_20pct_per_thrust_of_displacement(self):
        drive = _bind(SpinExtPlasmaDrive(thrust=1))
        assert drive.tons == pytest.approx(20.0)

    def test_cost_is_400k_per_ton(self):
        drive = _bind(SpinExtPlasmaDrive(thrust=1))
        assert drive.cost == pytest.approx(8_000_000.0)

    def test_power_equals_tons(self):
        drive = _bind(SpinExtPlasmaDrive(thrust=1))
        assert drive.power == pytest.approx(drive.tons)

    def test_fuel_tons_per_hour_is_1pct_per_thrust(self):
        drive = _bind(SpinExtPlasmaDrive(thrust=2))
        assert drive.fuel_tons_per_hour == pytest.approx(2.0)

    def test_item_description_includes_thrust(self):
        drive = _bind(SpinExtPlasmaDrive(thrust=3))
        assert drive.item_description() == 'SpinExt Plasma Drive, Thrust 3'


class TestSpinExtPlasmaDriveModifications:
    def test_energy_efficient_reduces_power_by_20pct(self):
        plain = _bind(SpinExtPlasmaDrive(thrust=1))
        eff = _bind(SpinExtPlasmaDrive(thrust=1, modifications=[SpinExtPlasmaDriveEnergyEfficient]))
        assert eff.power == pytest.approx(plain.power * 0.80)

    def test_size_reduction_reduces_tons_by_10pct(self):
        plain = _bind(SpinExtPlasmaDrive(thrust=1))
        reduced = _bind(SpinExtPlasmaDrive(thrust=1, modifications=[SpinExtPlasmaDriveSizeReduction]))
        assert reduced.tons == pytest.approx(plain.tons * 0.90)

    def test_fuel_efficient_reduces_fuel_by_20pct(self):
        plain = _bind(SpinExtPlasmaDrive(thrust=1))
        eff = _bind(SpinExtPlasmaDrive(thrust=1, modifications=[SpinExtPlasmaDriveFuelEfficient]))
        assert eff.fuel_tons_per_hour == pytest.approx(plain.fuel_tons_per_hour * 0.80)

    def test_item_description_lists_modifications(self):
        drive = _bind(
            SpinExtPlasmaDrive(
                thrust=2,
                modifications=[SpinExtPlasmaDriveSizeReduction, SpinExtPlasmaDriveFuelEfficient],
            )
        )
        assert drive.item_description() == 'SpinExt Plasma Drive, Thrust 2 (Size Reduction, Fuel Efficient)'

    def test_fuel_in_notes(self):
        drive = _bind(SpinExtPlasmaDrive(thrust=1))
        assert 'Uses standard liquid hydrogen fuel' in drive.notes.infos

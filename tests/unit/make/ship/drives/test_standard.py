"""Unit tests for drives/standard.py — MDrive concealed mode and drive modifications."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.drives.standard import (
    DecreasedFuel,
    EarlyJump,
    FuelEfficient,
    FuelInefficient,
    JumpEnergyInefficient,
    MDrive1,
    MDrive2,
    StealthJump,
)


class _Ship(ShipBase):
    def __init__(self, tl=12, displacement=200):
        super().__init__(tl=tl, displacement=displacement)


def _bind(part, tl=12, displacement=200):
    part.bind(_Ship(tl, displacement))
    return part


class TestMDriveConcealed:
    def test_effective_thrust_is_halved_when_concealed(self):
        drive = _bind(MDrive2(concealed=True))
        assert drive.effective_thrust == 1

    def test_concealed_tons_are_25pct_higher(self):
        plain = _bind(MDrive2())
        concealed = _bind(MDrive2(concealed=True))
        assert concealed.tons == pytest.approx(plain.tons * 1.25)

    def test_concealed_cost_is_25pct_higher(self):
        plain = _bind(MDrive2())
        concealed = _bind(MDrive2(concealed=True))
        assert concealed.cost == pytest.approx(plain.cost * 1.25)

    def test_concealed_note_describes_effective_thrust(self):
        drive = _bind(MDrive2(concealed=True))
        assert 'Concealed manoeuvre drive: effective Thrust 1' in drive.notes.infos

    def test_not_concealed_effective_thrust_equals_level(self):
        drive = _bind(MDrive2())
        assert drive.effective_thrust == 2


class TestMDriveSerialization:
    def test_computed_not_serialized(self):
        drive = MDrive1.model_validate({'drive_type': 'mdrive_1', 'tons': 999, 'cost': 999, 'power': 999})
        _bind(drive)
        dump = drive.model_dump()
        assert 'tons' not in dump
        assert 'cost' not in dump
        assert 'power' not in dump


class TestJDriveModifications:
    def test_decreased_fuel_delta_percent(self):
        assert DecreasedFuel.fuel_delta_percent == pytest.approx(-0.05)

    def test_fuel_efficient_delta_percent(self):
        assert FuelEfficient.fuel_delta_percent == pytest.approx(-0.20)

    def test_fuel_inefficient_delta_percent(self):
        assert FuelInefficient.fuel_delta_percent == pytest.approx(0.25)

    def test_early_jump_info_note(self):
        assert 'Can jump at the 90-diameter limit' in EarlyJump.info_notes

    def test_stealth_jump_info_note(self):
        assert 'Reduces jump emergence radiation signature' in StealthJump.info_notes

    def test_jump_energy_inefficient_power_multiplier(self):
        assert JumpEnergyInefficient.power_multiplier == pytest.approx(1.30)

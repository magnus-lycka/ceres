"""Unit tests for drives/standard.py — MDrive concealed mode and drive modifications."""

import pytest

from ceres.make.ship.base import ShipBase
from ceres.make.ship.drives.spinext import SpinExtPlasmaDrive
from ceres.make.ship.drives.standard import (
    DecreasedFuel,
    DriveSection,
    EarlyJump,
    FuelEfficient,
    FuelInefficient,
    JDrive2,
    JumpEnergyInefficient,
    LateJump,
    LimitedRange,
    MDrive0,
    MDrive1,
    MDrive2,
    MDrive3,
    OrbitalRange,
    RDrive2,
    SolarSail,
    SpinExtSolarSailTL8,
    StealthJump,
)
from ceres.make.ship.parts import Advanced, EnergyEfficient
from ceres.make.ship.spec import ShipSpec, SpecRow, SpecSection


class _Ship(ShipBase):
    tl: int = 12
    displacement: int = 200


class _PerformanceShip(_Ship):
    @property
    def performance_displacement(self) -> float:
        return 250.0


class _SpecShip(_Ship):
    def _spec_row_for_part(self, section, part, power=None, emphasize_power=False):
        return SpecRow(
            section=section,
            item=part.build_item() or type(part).__name__,
            tons=part.tons,
            power=part.power if power is None else power,
            cost=part.cost,
            emphasize_power=emphasize_power,
            notes=part.notes,
        )


def _bind(part, tl=12, displacement=200):
    part.bind(_Ship(tl=tl, displacement=displacement))
    return part


def _bind_to(part, ship):
    part.bind(ship)
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

    def test_level_zero_power_uses_fractional_thrust_rule(self):
        drive = _bind(MDrive0())
        assert drive.power == pytest.approx(5)

    def test_customisation_changes_tons_cost_and_power(self):
        drive = _bind(MDrive3(customisation=Advanced(modifications=[EnergyEfficient])))

        assert drive.tons == pytest.approx(6)
        assert drive.cost == pytest.approx(13_200_000)
        assert drive.power == pytest.approx(45)

    def test_performance_displacement_is_shown_when_larger_than_hull(self):
        drive = _bind_to(MDrive2(), _PerformanceShip())
        assert drive.build_item() == 'M-Drive 2 (250t)'

    def test_bulkhead_label_is_m_drive(self):
        assert MDrive2().bulkhead_label() == 'M-Drive'


class TestRDrive:
    def test_r_drive_uses_performance_displacement_for_tons_and_cost(self):
        drive = _bind_to(RDrive2(), _PerformanceShip())

        assert drive.build_item() == 'R-Drive Thrust 2'
        assert drive.tons == pytest.approx(10)
        assert drive.cost == pytest.approx(2_000_000)
        assert drive.power == 0
        assert drive.bulkhead_label() == 'R-Drive'

    def test_high_burn_thruster_changes_label_and_notes(self):
        drive = _bind(RDrive2(high_burn_thruster=True))

        assert drive.build_item() == 'High-Burn Thruster, Thrust 2'
        assert 'No inertial compensation above manoeuvre-drive thrust' in drive.notes.infos


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

    def test_range_modification_notes(self):
        assert 'This manoeuvre drive only functions within the 100-diameter limit' in LimitedRange.info_notes
        assert 'Operational range increased to orbital distances' in OrbitalRange.info_notes
        assert 'Requires the 150-diameter limit before jumping' in LateJump.info_notes

    def test_jump_drive_reports_parsecs_tons_cost_and_power(self):
        drive = _bind(JDrive2())

        assert drive.build_item() == 'Jump 2'
        assert drive.bulkhead_label() == 'Jump Drive'
        assert drive.parsecs == 2
        assert drive.tons == pytest.approx(15)
        assert drive.cost == pytest.approx(22_500_000)
        assert drive.power == pytest.approx(40)

    def test_jump_drive_customisation_changes_tons_cost_power_and_notes(self):
        drive = _bind(JDrive2(customisation=Advanced(modifications=[EnergyEfficient])))

        assert drive.tons == pytest.approx(15)
        assert drive.cost == pytest.approx(24_750_000)
        assert drive.power == pytest.approx(30)
        assert drive.notes.infos == ['Advanced: Energy Efficient']

    def test_jump_drive_performance_displacement_is_shown_when_larger_than_hull(self):
        drive = _bind_to(JDrive2(), _PerformanceShip())
        assert drive.build_item() == 'Jump 2 (250t)'


class TestSolarSails:
    def test_core_solar_sail_values_and_notes(self):
        sail = _bind(SolarSail())

        assert sail.tons == pytest.approx(10)
        assert sail.cost == pytest.approx(2_000_000)
        assert 'Effective Thrust 0 while using the solar sail as primary propulsion' in sail.notes.infos
        assert 'Jump drives cannot be engaged while the solar sail is deployed' in sail.notes.infos

    def test_spinext_solar_sail_without_panel_mode(self):
        sail = _bind(SpinExtSolarSailTL8(tons=20))

        assert sail.effective_thrust == pytest.approx(0.01)
        assert sail.output == 0
        assert sail.cost == pytest.approx(8_000_000)
        assert sail.power == 0
        assert sail.build_item() == 'SpinExt Solar Sail (TL 8), Thrust 0.01'
        assert 'Acts as solar panels for double cost at half same-tonnage solar panel Power' not in sail.notes.infos

    def test_spinext_solar_sail_panel_mode_adds_output_and_note(self):
        sail = _bind(SpinExtSolarSailTL8(tons=20, solar_panel_mode=True))

        assert sail.output == pytest.approx(20)
        assert sail.cost == pytest.approx(16_000_000)
        assert sail.build_item() == 'SpinExt Solar Sail (TL 8), Thrust 0.01, Power 20'
        assert 'Acts as solar panels for double cost at half same-tonnage solar panel Power' in sail.notes.infos


class TestDriveSection:
    def test_all_parts_excludes_missing_drives(self):
        section = DriveSection(m_drive=MDrive1(), j_drive=JDrive2())

        assert section._all_parts() == [section.m_drive, section.j_drive]

    def test_output_is_zero_without_solar_sail(self):
        assert DriveSection().output == 0

    def test_output_uses_solar_sail_output_when_present(self):
        assert DriveSection(solar_sail=SpinExtSolarSailTL8(tons=20, solar_panel_mode=True)).output == pytest.approx(20)

    def test_jump_control_validation_ignores_absent_jump_drive(self):
        section = DriveSection()

        section.validate_jump_control(None)

    def test_jump_control_validation_warns_when_missing(self):
        section = DriveSection(j_drive=JDrive2())

        section.validate_jump_control(None)

        assert section.j_drive is not None
        assert section.j_drive.notes.warnings == ['No Jump Control software']

    def test_jump_control_validation_warns_when_control_is_too_low(self):
        section = DriveSection(j_drive=JDrive2())

        section.validate_jump_control(1)

        assert section.j_drive is not None
        assert section.j_drive.notes.warnings == ['Limited to Jump 1 by control software']

    def test_jump_control_validation_accepts_adequate_control(self):
        section = DriveSection(j_drive=JDrive2())

        section.validate_jump_control(2)

        assert section.j_drive is not None
        assert section.j_drive.notes.warnings == []

    def test_add_spec_rows_places_drives_in_their_sections(self):
        ship = _SpecShip()
        section = DriveSection(m_drive=MDrive1(), r_drive=RDrive2(), j_drive=JDrive2())
        for part in section._all_parts():
            part.bind(ship)
        spec = ShipSpec()

        section.add_spec_rows(ship, spec)

        assert [row.item for row in spec.rows_for_section(SpecSection.JUMP)] == ['Jump 2']
        assert [row.item for row in spec.rows_for_section(SpecSection.PROPULSION)] == [
            'R-Drive Thrust 2',
            'M-Drive 1',
        ]

    def test_add_spec_rows_emphasizes_solar_sail_panel_output(self):
        ship = _SpecShip()
        sail = _bind_to(SpinExtSolarSailTL8(tons=20, solar_panel_mode=True), ship)
        section = DriveSection(solar_sail=sail)
        spec = ShipSpec()

        section.add_spec_rows(ship, spec)

        row = spec.row('SpinExt Solar Sail (TL 8), Thrust 0.01, Power 20', section=SpecSection.PROPULSION)
        assert row.power == pytest.approx(20)
        assert row.emphasize_power is True

    def test_add_spec_rows_includes_plasma_drive(self):
        ship = _SpecShip()
        plasma_drive = _bind_to(SpinExtPlasmaDrive(thrust=1), ship)
        section = DriveSection(plasma_drive=plasma_drive)
        spec = ShipSpec()

        section.add_spec_rows(ship, spec)

        assert [row.item for row in spec.rows_for_section(SpecSection.PROPULSION)] == ['SpinExt Plasma Drive, Thrust 1']

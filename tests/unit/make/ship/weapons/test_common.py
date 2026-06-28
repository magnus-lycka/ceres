"""Unit tests for weapons/common.py — MountWeapon types, customisation notes, _size_reduction_steps."""

import pytest

from ceres.make.ship.parts import Advanced, Budget, EnergyEfficient, HighTechnology, SizeReduction, VeryAdvanced
from ceres.make.ship.weapons.common import (
    FusionGun,
    HighYield,
    Inaccurate,
    IntenseFocus,
    LongRange,
    MissileRack,
    ParticleBeam,
    PulseLaser,
    Railgun,
    VeryHighYield,
    _size_reduction_steps,
)


class TestSizeReductionSteps:
    def test_true_counts_as_one(self):
        assert _size_reduction_steps(True) == 1

    def test_integer_returns_itself(self):
        assert _size_reduction_steps(3) == 3

    def test_false_counts_as_zero(self):
        assert _size_reduction_steps(False) == 0


class TestMountWeaponDeserialization:
    def test_union_discriminates_by_weapon_type(self):
        from ceres.make.ship.weapons.mounts import TripleTurret

        turret = TripleTurret.model_validate(
            {
                'turret_type': 'triple_turret',
                'weapons': [
                    {'weapon_type': 'fusion_gun'},
                    {'weapon_type': 'particle_beam'},
                    {'weapon_type': 'railgun'},
                ],
            }
        )
        assert [type(w) for w in turret.weapons] == [FusionGun, ParticleBeam, Railgun]

    def test_build_item_is_base_name_without_customisation(self):
        w = PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))
        assert w.build_item() == 'Pulse Laser'


class TestCustomisationNotes:
    def test_no_customisation_has_no_note(self):
        assert PulseLaser().customisation_note() is None

    def test_advanced_note_message(self):
        note = PulseLaser(customisation=Advanced(modifications=[EnergyEfficient])).customisation_note()
        assert note is not None
        assert note.message == 'Advanced: Energy Efficient'

    def test_very_advanced_note_message(self):
        note = PulseLaser(customisation=VeryAdvanced(modifications=[VeryHighYield])).customisation_note()
        assert note is not None
        assert note.message == 'Very Advanced: Very High Yield'

    def test_high_technology_note_message(self):
        laser = PulseLaser(customisation=HighTechnology(modifications=[VeryHighYield, EnergyEfficient]))
        note = laser.customisation_note()
        assert note is not None
        assert note.message == 'High Technology: Very High Yield, Energy Efficient'


class TestAllowedModifications:
    def test_accurate_is_allowed_and_noted(self):
        from ceres.make.ship.weapons.common import Accurate

        w = PulseLaser(customisation=VeryAdvanced(modifications=[Accurate]))
        assert 'Accurate weapons gain DM+1 to attack rolls' in w.notes.infos

    def test_inaccurate_reduces_cost(self):
        w = PulseLaser(customisation=Budget(modifications=[Inaccurate]))
        assert w.cost_modifier == pytest.approx(0.75)
        assert 'Inaccurate weapons suffer DM-1 to attack rolls' in w.notes.infos

    def test_intense_focus_allowed_for_lasers(self):
        w = PulseLaser(customisation=VeryAdvanced(modifications=[IntenseFocus]))
        assert 'Intense Focus is only applicable for laser and particle weapons' not in w.notes.errors
        assert 'Intense Focus weapons gain AP+2' in w.notes.infos

    def test_intense_focus_rejected_for_missile_rack(self):
        w = MissileRack(customisation=VeryAdvanced(modifications=[IntenseFocus]))
        assert 'Intense Focus is only applicable for laser and particle weapons' in w.notes.errors

    def test_high_yield_allowed_for_lasers(self):
        w = PulseLaser(customisation=Advanced(modifications=[HighYield]))
        assert 'Modification not allowed for MountWeapon: High Yield' not in w.notes.errors

    def test_high_yield_not_applicable_for_missile_rack(self):
        w = MissileRack(customisation=Advanced(modifications=[HighYield]))
        assert 'High Yield is not applicable for Missile Rack' in w.notes.errors

    def test_size_reduction_rejected(self):
        w = PulseLaser(customisation=Advanced(modifications=[SizeReduction]))
        assert 'Modification not allowed for MountWeapon: Size Reduction' in w.notes.errors

    def test_long_range_allowed_for_very_advanced(self):
        w = PulseLaser(customisation=VeryAdvanced(modifications=[LongRange]))
        assert 'Modification not allowed for MountWeapon: Long Range' not in w.notes.errors
        assert w.cost_modifier == pytest.approx(1.25)

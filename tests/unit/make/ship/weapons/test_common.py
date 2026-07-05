"""Unit tests for weapons/common.py — MountWeapon types, customisation notes, _size_reduction_steps."""

from typing import cast

import pytest

from ceres.make.ship.parts import Advanced, Budget, EnergyEfficient, HighTechnology, SizeReduction, VeryAdvanced
from ceres.make.ship.weapons.common import (
    BeamLaser,
    EasyToRepair,
    FusionGun,
    HighYield,
    Inaccurate,
    IntenseFocus,
    LaserDrill,
    LongRange,
    MissileRack,
    ParticleBeam,
    PlasmaGun,
    PulseLaser,
    Railgun,
    Resilient,
    Sandcaster,
    VeryHighYield,
    _damage_multiple_text,
    _mounted_weapon_cost,
    _mounted_weapon_label,
    _mounted_weapon_notes,
    _mounted_weapon_power,
    _size_reduction_steps,
)
from ceres.shared import NoteList


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


class TestMountedWeaponHelpers:
    def test_damage_multiple_text_is_omitted_when_not_applicable(self):
        assert _damage_multiple_text(None) is None

    def test_damage_multiple_text_describes_multiplier(self):
        assert _damage_multiple_text(3) == 'Damage × 3 after armour'

    def test_label_uses_weapon_build_item(self):
        assert _mounted_weapon_label(PulseLaser()) == 'Pulse Laser'

    def test_empty_weapon_notes_explain_absence(self):
        notes = cast(NoteList, _mounted_weapon_notes([], empty_message='No weapons mounted'))
        assert notes.infos == ['No weapons mounted']

    def test_weapon_notes_group_repeated_weapons_and_customisations(self):
        custom_laser = PulseLaser(customisation=Advanced(modifications=[EnergyEfficient]))
        notes = cast(
            NoteList,
            _mounted_weapon_notes(
                [PulseLaser(), PulseLaser(), custom_laser],
                empty_message='No weapons mounted',
            ),
        )

        assert notes.contents == ['Pulse Laser × 2', 'Pulse Laser']
        assert notes.infos == ['Advanced: Energy Efficient']

    def test_weapon_cost_and_power_sum_mounted_weapons(self):
        weapons = [
            PulseLaser(),
            BeamLaser(customisation=Advanced(modifications=[EnergyEfficient])),
        ]

        assert _mounted_weapon_cost(weapons) == pytest.approx(1_550_000)
        assert _mounted_weapon_power(weapons) == pytest.approx(7)


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

    def test_very_high_yield_not_applicable_for_missile_rack(self):
        w = MissileRack(customisation=VeryAdvanced(modifications=[VeryHighYield]))
        assert 'Very High Yield is not applicable for Missile Rack' in w.notes.errors

    def test_size_reduction_rejected(self):
        w = PulseLaser(customisation=Advanced(modifications=[SizeReduction]))
        assert 'Modification not allowed for MountWeapon: Size Reduction' in w.notes.errors

    def test_long_range_allowed_for_very_advanced(self):
        w = PulseLaser(customisation=VeryAdvanced(modifications=[LongRange]))
        assert 'Modification not allowed for MountWeapon: Long Range' not in w.notes.errors
        assert w.cost_modifier == pytest.approx(1.25)

    def test_easy_to_repair_and_resilient_notes_are_reported(self):
        w = PulseLaser(customisation=VeryAdvanced(modifications=[EasyToRepair, Resilient]))
        assert 'Easy to Repair weapons grant DM+1 to repair attempts' in w.notes.infos
        assert 'Resilient weapons reduce weapon critical hit Severity by -1' in w.notes.infos

    def test_invalid_customisation_notes_are_reported_on_weapon(self):
        w = PulseLaser(customisation=Advanced(modifications=[]))
        assert 'Advanced requires 1 advantage point(s) and 0 disadvantage point(s), got 0 and 0' in w.notes.errors


@pytest.mark.parametrize(
    ('weapon', 'description', 'base_cost', 'base_power'),
    [
        (PulseLaser(), 'Pulse Laser', 1_000_000, 4),
        (BeamLaser(), 'Beam Laser', 500_000, 4),
        (FusionGun(), 'Fusion Gun', 2_000_000, 12),
        (LaserDrill(), 'Laser Drill', 150_000, 4),
        (MissileRack(), 'Missile Rack', 750_000, 0),
        (ParticleBeam(), 'Particle Beam', 4_000_000, 8),
        (PlasmaGun(), 'Plasma Gun', 2_500_000, 6),
        (Railgun(), 'Railgun', 1_000_000, 2),
        (Sandcaster(), 'Sandcaster', 250_000, 0),
    ],
)
def test_mount_weapon_base_values(weapon, description, base_cost, base_power):
    assert weapon.build_item() == description
    assert weapon.weapon_cost == pytest.approx(base_cost)
    assert weapon.weapon_power == pytest.approx(base_power)

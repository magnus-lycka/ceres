"""Unit tests for make/robot/_robot_skill_base.py — _specs_to_display_dict and related helpers."""

from typing import ClassVar

import pytest

from ceres.character.domain import skills as _char
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Skill
from ceres.make.robot._robot_skill_base import (
    SpecKey,
    _best_dm,
    _field_characteristics,
    _RobotSkill,
    _skill_props_for_class,
    _specs_to_display_dict,
    _specs_to_multi_display_dict,
)


class _RobotAdmin(_RobotSkill):
    _char_cls: ClassVar[type[Skill] | None] = _char.Admin
    level: int = 0


class _RobotAstrogation(_RobotSkill):
    _char_cls: ClassVar[type[Skill] | None] = _char.Astrogation
    level: int = 0


class _RobotDrive(_RobotSkill):
    _char_cls: ClassVar[type[Skill] | None] = _char.Drive
    level: int = 0
    hovercraft: int = 0
    mole: int = 0
    track: int = 0
    walker: int = 0
    wheel: int = 0


class _RobotAthletics(_RobotSkill):
    _char_cls: ClassVar[type[Skill] | None] = _char.Athletics
    dexterity: int = 0
    endurance: int = 0
    strength: int = 0


class _CustomRobotSkill(_RobotSkill):
    _char_cls: ClassVar[type[Skill] | None] = None

    @classmethod
    def skill_name(cls) -> str:
        return 'Custom'


class TestSkillPropsForClass:
    def test_known_skill_returns_table_value(self):
        tl, bandwidth, cost = _skill_props_for_class(_char.Medic)
        assert tl == 9
        assert bandwidth == 0
        assert cost == pytest.approx(200.0)

    def test_unknown_skill_returns_default_props(self):
        class _FakeSkill:
            pass

        tl, bandwidth, cost = _skill_props_for_class(_FakeSkill)
        assert tl == 8
        assert bandwidth == 0
        assert cost == pytest.approx(100.0)

    def test_real_skill_without_table_entry_returns_default_props(self):
        tl, bandwidth, cost = _skill_props_for_class(_char.VaccSuit)
        assert tl == 8
        assert bandwidth == 0
        assert cost == pytest.approx(100.0)

    def test_high_bandwidth_skill(self):
        _tl, bandwidth, _cost = _skill_props_for_class(_char.Astrogation)
        assert bandwidth == 1

    def test_concrete_skill_inside_union_key_uses_matching_table_value(self):
        tl, bandwidth, cost = _skill_props_for_class(_char.PerformingArt)
        assert tl == 10
        assert bandwidth == 0
        assert cost == pytest.approx(500.0)


class TestFieldCharacteristic:
    def test_gun_combat_is_dex_based(self):
        assert _field_characteristics(_char.GunCombat, 'slug') == (Chars.DEX,)

    def test_athletics_strength_is_str_based(self):
        assert _field_characteristics(_char.Athletics, 'strength') == (Chars.STR,)

    def test_athletics_endurance_is_null(self):
        assert _field_characteristics(_char.Athletics, 'endurance') == ()

    def test_non_dex_skill_defaults_to_int_based(self):
        # Astrogation is not in _DEX_SKILLS; any field not in a special-case set falls through to INT
        assert _field_characteristics(_char.Astrogation, 'level') == (Chars.INT,)

    def test_animals_training_is_int_based(self):
        assert _field_characteristics(_char.Animals, 'training') == (Chars.INT,)

    def test_pilot_spacecraft_is_dex_based(self):
        assert _field_characteristics(_char.Pilot, 'spacecraft') == (Chars.DEX,)

    def test_melee_may_use_strength_or_dexterity(self):
        # refs/core/03_combat.md — '2D + Melee (appropriate speciality) + STR or DEX DM'.
        assert _field_characteristics(_char.Melee, 'unarmed') == (Chars.STR, Chars.DEX)

    def test_best_dm_of_the_applicable_characteristics_applies(self):
        assert _best_dm((Chars.STR, Chars.DEX), {Chars.STR: 3, Chars.DEX: 1}) == 3
        assert _best_dm((Chars.STR, Chars.DEX), {Chars.STR: -1, Chars.DEX: 2}) == 2
        assert _best_dm((Chars.DEX,), {Chars.STR: 3, Chars.DEX: 1}) == 1
        assert _best_dm((), {Chars.STR: 3}) == 0


class TestSpecsToDisplayDict:
    def test_no_speciality_shows_skill_name_and_level(self):
        result = _specs_to_display_dict({(_char.Admin, None, None): 2})
        assert result == {'Admin': 2}

    def test_all_specialities_same_level_shows_all_label(self):
        specialities = _char.Drive.specialities()
        per_spec: dict[SpecKey, int] = {(_char.Drive, None, s): 2 for s in specialities}
        result = _specs_to_display_dict(per_spec)
        assert 'Drive (All)' in result
        assert result['Drive (All)'] == 2

    def test_all_specialities_at_zero_shows_base_name(self):
        specialities = _char.Drive.specialities()
        per_spec: dict[SpecKey, int] = {(_char.Drive, None, s): 0 for s in specialities}
        result = _specs_to_display_dict(per_spec)
        assert result.get('Drive') == 0

    def test_mixed_speciality_levels_shows_individual_entries(self):
        specialities = list(_char.Drive.specialities())
        per_spec: dict[SpecKey, int] = {
            (_char.Drive, None, specialities[0]): 2,
            (_char.Drive, None, specialities[1]): 1,
        }
        result = _specs_to_display_dict(per_spec)
        assert f'Drive ({specialities[0]})' in result
        assert result[f'Drive ({specialities[0]})'] == 2

    def test_majority_baseline_compacts_to_other(self):
        # One speciality above a common baseline: name the outlier, compact the rest.
        specialities = list(_char.Melee.specialities())
        per_spec: dict[SpecKey, int] = {(_char.Melee, None, s): 1 for s in specialities}
        per_spec[(_char.Melee, None, 'Unarmed')] = 3
        result = _specs_to_display_dict(per_spec)
        assert result == {'Melee (Unarmed)': 3, 'Melee (Other)': 1}

    def test_two_outliers_above_the_baseline_are_both_named(self):
        per_spec: dict[SpecKey, int] = {(_char.Melee, None, s): 1 for s in _char.Melee.specialities()}
        per_spec[(_char.Melee, None, 'Unarmed')] = 3
        per_spec[(_char.Melee, None, 'Blade')] = 2
        result = _specs_to_display_dict(per_spec)
        assert result == {'Melee (Unarmed)': 3, 'Melee (Blade)': 2, 'Melee (Other)': 1}

    def test_other_not_used_when_specialities_are_partial(self):
        # Only some specialities present: '(Other)' would overstate coverage.
        specialities = list(_char.Drive.specialities())
        per_spec: dict[SpecKey, int] = {
            (_char.Drive, None, specialities[0]): 3,
            (_char.Drive, None, specialities[1]): 1,
            (_char.Drive, None, specialities[2]): 1,
        }
        result = _specs_to_display_dict(per_spec)
        assert 'Drive (Other)' not in result
        assert result[f'Drive ({specialities[1]})'] == 1

    def test_zero_level_baseline_stays_excluded(self):
        specialities = list(_char.Melee.specialities())
        per_spec: dict[SpecKey, int] = {(_char.Melee, None, s): 0 for s in specialities}
        per_spec[(_char.Melee, None, 'Unarmed')] = 2
        result = _specs_to_display_dict(per_spec)
        assert result == {'Melee (Unarmed)': 2}

    def test_all_equal_still_compacts_to_all(self):
        specialities = list(_char.Melee.specialities())
        per_spec: dict[SpecKey, int] = {(_char.Melee, None, s): 2 for s in specialities}
        result = _specs_to_display_dict(per_spec)
        assert result == {'Melee (All)': 2}

    def test_negative_reading_is_dropped_from_a_multi_reading_entry(self):
        # A weak manipulator can make one reading negative; only the usable ones list.
        per_spec: dict[SpecKey, int] = {
            (_char.Melee, None, s): 2 if s == 'Unarmed' else 0 for s in _char.Melee.specialities()
        }
        alt: dict[SpecKey, int] = {
            (_char.Melee, None, s): 2 if s == 'Unarmed' else -1 for s in _char.Melee.specialities()
        }
        assert _specs_to_multi_display_dict([per_spec, alt]) == {'Melee (Unarmed)': '2'}

    def test_entry_with_only_negative_readings_is_dropped(self):
        per_spec: dict[SpecKey, int] = {(_char.Melee, None, s): -1 for s in _char.Melee.specialities()}
        assert _specs_to_display_dict(per_spec) == {}

    def test_no_speciality_skill_at_negative_is_dropped(self):
        assert _specs_to_display_dict({(_char.Medic, None, None): -1}) == {}

    def test_no_speciality_skill_at_zero_is_kept(self):
        # Level 0 is trained (DM+0), materially different from untrained — never dropped.
        assert _specs_to_display_dict({(_char.Medic, None, None): 0}) == {'Medic': 0}

    def test_negative_baseline_does_not_become_an_other_group(self):
        per_spec: dict[SpecKey, int] = {
            (_char.Melee, None, s): 3 if s == 'Unarmed' else 1 for s in _char.Melee.specialities()
        }
        alt: dict[SpecKey, int] = {
            (_char.Melee, None, s): 3 if s == 'Unarmed' else -2 for s in _char.Melee.specialities()
        }
        result = _specs_to_multi_display_dict([per_spec, alt])
        assert result == {'Melee (Unarmed)': '3', 'Melee (Other)': '1'}

    def test_level_zero_speciality_excluded_in_mixed(self):
        specialities = list(_char.Drive.specialities())
        per_spec: dict[SpecKey, int] = {
            (_char.Drive, None, specialities[0]): 1,
            (_char.Drive, None, specialities[1]): 0,
        }
        result = _specs_to_display_dict(per_spec)
        assert f'Drive ({specialities[1]})' not in result


class TestRobotSkill:
    def test_skill_name_comes_from_character_skill_class(self):
        assert _RobotAdmin.skill_name() == 'Admin'

    def test_skill_name_requires_character_skill_or_override(self):
        class _NamelessRobotSkill(_RobotSkill):
            _char_cls: ClassVar[type[Skill] | None] = None

        with pytest.raises(NotImplementedError, match='_NamelessRobotSkill must override skill_name'):
            _NamelessRobotSkill.skill_name()

    def test_inactive_skill_uses_base_bandwidth_cost_and_tl(self):
        skill = _RobotAdmin()

        assert skill.bandwidth == 0
        assert skill.cost == 100.0
        assert skill.tl == 8

    def test_active_skill_uses_level_for_bandwidth_and_scaled_cost(self):
        skill = _RobotAdmin(level=2)

        assert skill.bandwidth == 2
        assert skill.cost == 10_000.0

    def test_active_high_bandwidth_skill_adds_level_to_base_bandwidth(self):
        skill = _RobotAstrogation(level=2)

        assert skill.bandwidth == 3
        assert skill.cost == 50_000.0
        assert skill.tl == 12

    def test_package_entries_name_a_multi_characteristic_skill_once(self):
        # The ledger records the purchase; Melee is one package, not one per characteristic.
        from ceres.make.robot.skills import Melee

        assert Melee(unarmed=2).package_entries() == {'Melee (Unarmed)': 2}

    def test_package_entries_ignore_characteristic_dms(self):
        from ceres.make.robot.skills import Melee

        pkg = Melee(unarmed=2)
        assert pkg.package_entries() == pkg.package_entries()
        assert pkg.display_entries({Chars.STR: 3}) != pkg.package_entries()

    def test_no_speciality_raw_entries_apply_default_int_dm_unclamped(self):
        # Raw entries keep negative readings; the display layer drops them rather than
        # clamping, which would claim a competence the robot does not have.
        assert _RobotAdmin(level=1)._per_spec_raw({Chars.INT: 2}) == {(_char.Admin, None, None): 3}
        assert _RobotAdmin(level=1)._per_spec_raw({Chars.INT: -3}) == {(_char.Admin, None, None): -2}

    def test_speciality_raw_entries_use_field_levels(self):
        raw = _RobotDrive(track=2, wheel=1)._per_spec_raw({})

        assert raw is not None
        assert raw[(_char.Drive, None, 'Track')] == 2
        assert raw[(_char.Drive, None, 'Wheel')] == 1
        assert raw[(_char.Drive, None, 'Hovercraft')] == 0

    def test_speciality_raw_entries_skip_null_character_fields(self):
        raw = _RobotAthletics(dexterity=1, endurance=3, strength=2)._per_spec_raw({})

        assert raw is not None
        assert raw[(_char.Athletics, None, 'Dexterity')] == 1
        assert raw[(_char.Athletics, None, 'Strength')] == 2
        assert (_char.Athletics, None, 'Endurance') not in raw

    def test_speciality_level_field_applies_to_every_speciality(self):
        assert _RobotDrive(level=1).display_entries({}) == {'Drive (All)': 1}

    def test_speciality_display_entries_apply_characteristic_dms(self):
        skill = _RobotDrive(track=2, wheel=1)

        # Hovercraft, Mole and Walker share the DM-only baseline of 1 and compact to (Other).
        assert skill.display_entries({Chars.DEX: 1}) == {
            'Drive (Other)': 1,
            'Drive (Track)': 3,
            'Drive (Wheel)': 2,
        }

    def test_custom_skill_without_character_class_manages_own_display(self):
        assert _CustomRobotSkill()._per_spec_raw({}) is None
        assert _CustomRobotSkill().display_entries({}) == {'Custom': 0}

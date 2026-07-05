"""Unit tests for make/robot/_robot_skill_base.py — _specs_to_display_dict and related helpers."""

from typing import ClassVar

import pytest

from ceres.character.domain import skills as _char
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Skill
from ceres.make.robot._robot_skill_base import (
    _field_characteristic,
    _RobotSkill,
    _skill_props_for_class,
    _specs_to_display_dict,
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
        assert _field_characteristic(_char.GunCombat, 'slug') == Chars.DEX

    def test_athletics_strength_is_str_based(self):
        assert _field_characteristic(_char.Athletics, 'strength') == Chars.STR

    def test_athletics_endurance_is_null(self):
        assert _field_characteristic(_char.Athletics, 'endurance') is None

    def test_non_dex_skill_defaults_to_int_based(self):
        # Astrogation is not in _DEX_SKILLS; any field not in a special-case set falls through to INT
        assert _field_characteristic(_char.Astrogation, 'level') == Chars.INT

    def test_animals_training_is_int_based(self):
        assert _field_characteristic(_char.Animals, 'training') == Chars.INT

    def test_pilot_spacecraft_is_dex_based(self):
        assert _field_characteristic(_char.Pilot, 'spacecraft') == Chars.DEX


class TestSpecsToDisplayDict:
    def test_no_speciality_shows_skill_name_and_level(self):
        result = _specs_to_display_dict({(_char.Admin, None): 2})
        assert result == {'Admin': 2}

    def test_all_specialities_same_level_shows_all_label(self):
        specialities = _char.Drive.specialities()
        per_spec: dict[tuple[type[Skill], str | None], int] = {(_char.Drive, s): 2 for s in specialities}
        result = _specs_to_display_dict(per_spec)
        assert 'Drive (All)' in result
        assert result['Drive (All)'] == 2

    def test_all_specialities_at_zero_shows_base_name(self):
        specialities = _char.Drive.specialities()
        per_spec: dict[tuple[type[Skill], str | None], int] = {(_char.Drive, s): 0 for s in specialities}
        result = _specs_to_display_dict(per_spec)
        assert result.get('Drive') == 0

    def test_mixed_speciality_levels_shows_individual_entries(self):
        specialities = list(_char.Drive.specialities())
        per_spec: dict[tuple[type[Skill], str | None], int] = {
            (_char.Drive, specialities[0]): 2,
            (_char.Drive, specialities[1]): 1,
        }
        result = _specs_to_display_dict(per_spec)
        assert f'Drive ({specialities[0]})' in result
        assert result[f'Drive ({specialities[0]})'] == 2

    def test_level_zero_speciality_excluded_in_mixed(self):
        specialities = list(_char.Drive.specialities())
        per_spec: dict[tuple[type[Skill], str | None], int] = {
            (_char.Drive, specialities[0]): 1,
            (_char.Drive, specialities[1]): 0,
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

    def test_no_speciality_raw_entries_apply_default_int_dm_and_floor_at_zero(self):
        assert _RobotAdmin(level=1)._per_spec_raw({Chars.INT: 2}) == {(_char.Admin, None): 3}
        assert _RobotAdmin(level=1)._per_spec_raw({Chars.INT: -3}) == {(_char.Admin, None): 0}

    def test_speciality_raw_entries_use_field_levels(self):
        raw = _RobotDrive(track=2, wheel=1)._per_spec_raw({})

        assert raw is not None
        assert raw[(_char.Drive, 'Track')] == 2
        assert raw[(_char.Drive, 'Wheel')] == 1
        assert raw[(_char.Drive, 'Hovercraft')] == 0

    def test_speciality_raw_entries_skip_null_character_fields(self):
        raw = _RobotAthletics(dexterity=1, endurance=3, strength=2)._per_spec_raw({})

        assert raw is not None
        assert raw[(_char.Athletics, 'Dexterity')] == 1
        assert raw[(_char.Athletics, 'Strength')] == 2
        assert (_char.Athletics, 'Endurance') not in raw

    def test_speciality_level_field_applies_to_every_speciality(self):
        assert _RobotDrive(level=1).display_entries({}) == {'Drive (All)': 1}

    def test_speciality_display_entries_apply_characteristic_dms(self):
        skill = _RobotDrive(track=2, wheel=1)

        assert skill.display_entries({Chars.DEX: 1}) == {
            'Drive (Hovercraft)': 1,
            'Drive (Mole)': 1,
            'Drive (Track)': 3,
            'Drive (Walker)': 1,
            'Drive (Wheel)': 2,
        }

    def test_custom_skill_without_character_class_manages_own_display(self):
        assert _CustomRobotSkill()._per_spec_raw({}) is None
        assert _CustomRobotSkill().display_entries({}) == {'Custom': 0}

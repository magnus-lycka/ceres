"""Unit tests for make/robot/_robot_skill_base.py — _specs_to_display_dict and related helpers."""

import pytest

from ceres.character.domain import skills as _char
from ceres.character.domain.characteristics import Chars
from ceres.character.domain.skills import Skill
from ceres.make.robot._robot_skill_base import (
    _field_characteristic,
    _skill_props_for_class,
    _specs_to_display_dict,
)


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

    def test_high_bandwidth_skill(self):
        _tl, bandwidth, _cost = _skill_props_for_class(_char.Astrogation)
        assert bandwidth == 1


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

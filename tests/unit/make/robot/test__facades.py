"""Unit tests for make/robot/_facades.py — robot skill facade skill_name and bandwidth."""

from ceres.make.robot._facades import (
    Admin,
    Astrogation,
    Electronics,
    GunCombat,
    Pilot,
)
from ceres.make.robot._robot_skill_base import _skill_props_for_class


class TestSkillName:
    def test_admin_skill_name(self):
        assert Admin.skill_name() == 'Admin'

    def test_astrogation_skill_name(self):
        assert Astrogation.skill_name() == 'Astrogation'

    def test_pilot_skill_name(self):
        assert Pilot.skill_name() == 'Pilot'


class TestBandwidth:
    def test_admin_zero_bandwidth_when_not_active(self):
        assert Admin().bandwidth == 0

    def test_admin_bandwidth_increases_with_level(self):
        assert Admin(level=2).bandwidth == 2

    def test_astrogation_base_bandwidth_is_one(self):
        assert Astrogation().bandwidth == 1

    def test_electronics_speciality_bandwidth(self):
        skill = Electronics(comms=1, computers=2)
        assert skill.bandwidth == 3


class TestSpecialityFields:
    def test_electronics_has_sensors_field(self):
        skill = Electronics(sensors=3)
        assert skill.sensors == 3

    def test_gun_combat_specialities_default_to_zero(self):
        skill = GunCombat()
        assert skill.level == 0

    def test_pilot_spacecraft_can_be_set(self):
        skill = Pilot(spacecraft=2)
        assert skill.spacecraft == 2


class TestSkillPropsAlignment:
    def test_astrogation_is_high_bandwidth(self):
        _, bandwidth, _ = _skill_props_for_class(Astrogation._char_cls)
        assert bandwidth == 1

    def test_admin_is_zero_bandwidth(self):
        _, bandwidth, _ = _skill_props_for_class(Admin._char_cls)
        assert bandwidth == 0

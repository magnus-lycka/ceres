"""Tests for Robot aggregate properties.

All expected values are derived from Traveller Robot Handbook rules:
  - Size table:        refs/robot/04_chassis.md
  - Locomotion table:  refs/robot/05_locomotion.md
  - Armour table:      refs/robot/07_chassis_options.md (TL band → Base Protection)
  - Endurance:         refs/robot/07_chassis_options.md (TL modifier table)
"""

from typing import Any, ClassVar, Literal

import pytest

from ceres.make.robot.chassis import Trait
from ceres.make.robot.parts import RobotPart
from ceres.make.robot.skills import SkillGrant


class _SlottedPart(RobotPart):
    """Two-slot part used to test used_slots, remaining_slots, and slot overload."""

    type: Literal['SLOTTED'] = 'SLOTTED'
    tl: int = 5
    slots: ClassVar[int] = 2

    def build_item(self) -> str | None:
        return None


class _TraitPart(RobotPart):
    """Part that injects an ATV trait — used to test option trait aggregation."""

    type: Literal['TRAIT_PART'] = 'TRAIT_PART'
    tl: int = 5

    @property
    def robot_traits(self) -> tuple[Trait, ...]:
        return (Trait('ATV'),)

    def build_item(self) -> str | None:
        return None


class _SkillPart(RobotPart):
    """Part that grants Recon 1 — used to test option skill aggregation."""

    type: Literal['SKILL_PART'] = 'SKILL_PART'
    tl: int = 5

    @property
    def skill_grants(self) -> tuple[SkillGrant, ...]:
        return (SkillGrant('Recon', 1),)

    def build_item(self) -> str | None:
        return None


def make_robot(**kwargs):
    from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion

    defaults: dict[str, Any] = {
        'name': 'Test Robot',
        'tl': 8,
        'size': RobotSize.SIZE_3,
        'locomotion': WheelsLocomotion(),
        'brain': PrimitiveBrain(),
    }
    defaults.update(kwargs)
    return Robot(**defaults)


class TestAvailableSlots:
    """refs/robot/05_locomotion.md: None locomotion adds 25% (rounded up) to available slots."""

    def test_size3_wheels(self):
        # Size 3 = 4 base slots, Wheels = no bonus
        from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion

        robot = Robot(
            name='X',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
        )
        assert robot.available_slots == 4

    def test_size1_none_locomotion(self):
        # Size 1 = 1 base slot, None = ceil(1 * 1.25) = 2
        from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=12,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=AdvancedBrain(),
        )
        assert robot.available_slots == 2

    def test_size4_none_locomotion(self):
        # Size 4 = 8 base slots, None = ceil(8 * 1.25) = 10
        from ceres.make.robot import NoneLocomotion, PrimitiveBrain, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=8,
            size=RobotSize.SIZE_4,
            locomotion=NoneLocomotion(),
            brain=PrimitiveBrain(),
        )
        assert robot.available_slots == 10


class TestBaseHits:
    """refs/robot/04_chassis.md — Robot Size table."""

    @pytest.mark.parametrize(
        'size_val, expected_hits',
        [
            (1, 1),
            (2, 4),
            (3, 8),
            (4, 12),
            (5, 20),
            (6, 32),
            (7, 50),
            (8, 72),
        ],
    )
    def test_base_hits_by_size(self, size_val, expected_hits):
        from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion

        robot = Robot(
            name='X',
            tl=8,
            size=RobotSize(size_val),
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
        )
        assert robot.base_hits == expected_hits


class TestBaseArmour:
    """refs/robot/07_chassis_options.md — Robot Armour table (TL band → Base Protection)."""

    @pytest.mark.parametrize(
        'tl, expected_protection',
        [
            (6, 2),
            (7, 2),
            (8, 2),  # TL 6–8: Base Protection 2
            (9, 3),
            (10, 3),
            (11, 3),  # TL 9–11: Base Protection 3
            (12, 4),
            (13, 4),
            (14, 4),  # TL 12–14: Base Protection 4
            (15, 4),
            (16, 4),
            (17, 4),  # TL 15–17: Base Protection 4
            (18, 5),  # TL 18+: Base Protection 5
        ],
    )
    def test_base_armour_by_tl(self, tl, expected_protection):
        from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion

        robot = Robot(
            name='X',
            tl=tl,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
        )
        assert robot.base_armour == expected_protection


class TestBaseEndurance:
    """refs/robot/05_locomotion.md base endurance × refs/robot/07_chassis_options.md TL modifier."""

    def test_wheels_tl8_no_tl_bonus(self):
        # Wheels base endurance 72h, TL8 → multiplier 1.0 → 72h
        from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion

        robot = Robot(
            name='X',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
        )
        assert robot.base_endurance == 72.0

    def test_none_tl12_tl_bonus(self):
        # None base endurance 216h, TL12 → multiplier 1.5 → 324h
        from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=12,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=AdvancedBrain(),
        )
        assert robot.base_endurance == 324.0

    def test_none_tl15_tl_bonus(self):
        # None base endurance 216h, TL15 → multiplier 2.0 → 432h
        from ceres.make.robot import NoneLocomotion, PrimitiveBrain, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=15,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=PrimitiveBrain(),
        )
        assert robot.base_endurance == 432.0

    def test_grav_tl12(self):
        # Grav base endurance 24h, TL12 → multiplier 1.5 → 36h
        from ceres.make.robot import AdvancedBrain, GravLocomotion, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=12,
            size=RobotSize.SIZE_5,
            locomotion=GravLocomotion(),
            brain=AdvancedBrain(),
        )
        assert robot.base_endurance == 36.0


class TestBaseChassisCoct:
    """Base Chassis Cost = basic_cost (size) × cost_multiplier (locomotion).
    refs/robot/04_chassis.md and refs/robot/05_locomotion.md.
    """

    def test_size3_wheels(self):
        # Size 3 basic cost Cr400, Wheels multiplier x2 → Cr800
        from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion

        robot = Robot(
            name='X',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
        )
        assert robot.base_chassis_cost == 800.0

    def test_size1_none(self):
        # Size 1 basic cost Cr100, None multiplier x1 → Cr100
        from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=12,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=AdvancedBrain(),
        )
        assert robot.base_chassis_cost == 100.0

    def test_size5_grav(self):
        # Size 5 basic cost Cr1000, Grav multiplier x20 → Cr20000
        from ceres.make.robot import AdvancedBrain, GravLocomotion, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=12,
            size=RobotSize.SIZE_5,
            locomotion=GravLocomotion(),
            brain=AdvancedBrain(),
        )
        assert robot.base_chassis_cost == 20_000.0


class TestTraits:
    """Traits are assembled from armour, size, and locomotion."""

    def test_size3_tl8_wheels_traits(self):
        # Armour (+2) from TL8, Small (-2) from Size 3, no locomotion traits for Wheels
        from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion

        robot = Robot(
            name='X',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
        )
        trait_strs = [str(t) for t in robot.traits]
        assert 'Armour (+2)' in trait_strs
        assert 'Small (-2)' in trait_strs
        assert not any('Flyer' in s or 'ATV' in s for s in trait_strs)

    def test_size1_tl12_none_traits(self):
        # Armour (+4) from TL12, Small (-4) from Size 1, None locomotion has no traits
        from ceres.make.robot import AdvancedBrain, NoneLocomotion, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=12,
            size=RobotSize.SIZE_1,
            locomotion=NoneLocomotion(),
            brain=AdvancedBrain(),
        )
        trait_strs = [str(t) for t in robot.traits]
        assert 'Armour (+4)' in trait_strs
        assert 'Small (-4)' in trait_strs

    def test_grav_has_flyer_trait(self):
        from ceres.make.robot import AdvancedBrain, GravLocomotion, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=12,
            size=RobotSize.SIZE_5,
            locomotion=GravLocomotion(),
            brain=AdvancedBrain(),
        )
        trait_strs = [str(t) for t in robot.traits]
        assert any('Flyer' in s for s in trait_strs)

    def test_size5_no_size_trait(self):
        from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion

        robot = Robot(
            name='X',
            tl=8,
            size=RobotSize.SIZE_5,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
        )
        trait_strs = [str(t) for t in robot.traits]
        assert not any('Small' in s or 'Large' in s for s in trait_strs)


class TestLocomotionTlCheck:
    """A robot whose TL is below the locomotion's required TL should carry an error note."""

    def test_grav_below_tl9_is_error(self):
        from ceres.make.robot import GravLocomotion, PrimitiveBrain, Robot, RobotSize

        robot = Robot(
            name='X',
            tl=8,
            size=RobotSize.SIZE_3,
            locomotion=GravLocomotion(),
            brain=PrimitiveBrain(),
        )
        assert robot.notes.errors

    def test_wheels_at_tl5_no_error(self):
        from ceres.make.robot import PrimitiveBrain, Robot, RobotSize, WheelsLocomotion

        robot = Robot(
            name='X',
            tl=5,
            size=RobotSize.SIZE_3,
            locomotion=WheelsLocomotion(),
            brain=PrimitiveBrain(),
        )
        assert not robot.notes.errors


class TestBaseSlots:
    def test_size3_base_slots(self):
        from ceres.make.robot import RobotSize

        robot = make_robot(size=RobotSize.SIZE_3)
        assert robot.base_slots == 4

    def test_size5_base_slots(self):
        from ceres.make.robot import RobotSize

        robot = make_robot(size=RobotSize.SIZE_5)
        assert robot.base_slots == 16


class TestHits:
    def test_hits_equals_base_hits(self):
        from ceres.make.robot import RobotSize

        robot = make_robot(size=RobotSize.SIZE_4)
        assert robot.hits == robot.base_hits == 12


class TestOptions:
    def test_parts_of_type(self):
        part = _SlottedPart()
        robot = make_robot(options=[part])
        result = robot.parts_of_type(_SlottedPart)
        assert result == [part]

    def test_parts_of_type_empty_for_missing_type(self):
        robot = make_robot()
        assert robot.parts_of_type(_SlottedPart) == []

    def test_option_bound_on_post_init(self):
        part = _SlottedPart()
        robot = make_robot(options=[part])
        assert part.assembly is robot

    def test_option_traits_included_in_traits(self):
        robot = make_robot(options=[_TraitPart()])
        trait_names = [t.name for t in robot.traits]
        assert 'ATV' in trait_names

    def test_used_slots_with_slotted_option(self):
        from ceres.make.robot import RobotSize

        robot = make_robot(size=RobotSize.SIZE_3, options=[_SlottedPart()])
        assert robot.used_slots == 2

    def test_remaining_slots_with_slotted_option(self):
        from ceres.make.robot import RobotSize

        # Size 3, Wheels: 4 available − 2 used = 2 remaining
        robot = make_robot(size=RobotSize.SIZE_3, options=[_SlottedPart()])
        assert robot.remaining_slots == 2

    def test_no_options_remaining_equals_available(self):
        from ceres.make.robot import RobotSize

        robot = make_robot(size=RobotSize.SIZE_3)
        assert robot.remaining_slots == robot.available_slots == 4

    def test_slot_overload_produces_note(self):
        from ceres.make.robot import RobotSize

        # Size 1, Wheels: 1 available, _SlottedPart uses 2 → overload
        robot = make_robot(size=RobotSize.SIZE_1, options=[_SlottedPart()])
        errors = robot.build_notes()
        assert errors

    def test_bandwidth_overload_produces_note(self):
        from ceres.make.robot.brain import AdvancedBrain
        from ceres.make.robot.skills import SkillPackage

        # Advanced TL12 has bandwidth 2; installing 3 × bandwidth-1 packages overloads
        brain = AdvancedBrain(
            brain_tl=12,
            installed_skills=(
                SkillPackage(name='Recon', level=1, bandwidth=1),
                SkillPackage(name='Mechanic', level=1, bandwidth=1),
                SkillPackage(name='Medic', level=1, bandwidth=1),
            ),
        )
        robot = make_robot(brain=brain)
        notes = robot.build_notes()
        assert any('Bandwidth overload' in str(n) for n in notes)

    def test_remaining_slots_no_info_note(self):
        robot = make_robot()  # remaining slots > 0 but no info note — shown in Finalisation only
        notes = robot.build_notes()
        assert not any('remaining' in str(n).lower() and 'slot' in str(n).lower() for n in notes)

    def test_remaining_bandwidth_no_info_note(self):
        from ceres.make.robot.brain import AdvancedBrain

        robot = make_robot(brain=AdvancedBrain(brain_tl=12))  # remaining BW but no info note
        notes = robot.build_notes()
        assert not any('bandwidth remaining' in str(n).lower() for n in notes)

    def test_cost_raised_to_minimum_produces_info_note(self):
        from ceres.make.robot import NoneLocomotion, RobotSize

        # Size 1 NoneLocomotion, no manipulators: chassis Cr100 + brain Cr100 − discount Cr200 = 0
        # → raised to Basic Cost minimum Cr100
        robot = make_robot(size=RobotSize.SIZE_1, locomotion=NoneLocomotion(), manipulators=[])
        notes = robot.build_notes()
        assert any('Basic Cost' in str(n) for n in notes)


class TestFinalisationDetailSection:
    def test_finalisation_section_present(self):
        robot = make_robot()
        spec = robot.build_spec()
        titles = [s.title for s in spec.detail_sections]
        assert 'Finalisation' in titles

    def test_finalisation_has_remaining_row(self):
        robot = make_robot()
        spec = robot.build_spec()
        fin = next(s for s in spec.detail_sections if s.title == 'Finalisation')
        assert any(r.name == 'Remaining' for r in fin.rows)

    def test_finalisation_remaining_row_shows_bandwidth_for_advanced_brain(self):
        from ceres.make.robot.brain import AdvancedBrain

        robot = make_robot(brain=AdvancedBrain(brain_tl=12))
        spec = robot.build_spec()
        fin = next(s for s in spec.detail_sections if s.title == 'Finalisation')
        remaining = next(r for r in fin.rows if r.name == 'Remaining')
        assert remaining.col3 != '—'

    def test_finalisation_remaining_row_no_bandwidth_for_primitive_brain(self):
        from ceres.make.robot.brain import PrimitiveBrain

        robot = make_robot(brain=PrimitiveBrain())
        spec = robot.build_spec()
        fin = next(s for s in spec.detail_sections if s.title == 'Finalisation')
        remaining = next(r for r in fin.rows if r.name == 'Remaining')
        assert remaining.col3 == '—'

    def test_finalisation_total_row_shows_cost(self):
        robot = make_robot()
        spec = robot.build_spec()
        fin = next(s for s in spec.detail_sections if s.title == 'Finalisation')
        total_row = next(r for r in fin.rows if r.name == 'Total')
        assert total_row.cost != '—'

    def test_finalisation_cost_floor_row_shown_when_applied(self):
        from ceres.make.robot import NoneLocomotion, RobotSize

        robot = make_robot(size=RobotSize.SIZE_1, locomotion=NoneLocomotion(), manipulators=[])
        spec = robot.build_spec()
        fin = next(s for s in spec.detail_sections if s.title == 'Finalisation')
        assert any('Basic Cost' in r.name for r in fin.rows)


class TestBuildSpec:
    def test_spec_name(self):

        robot = make_robot(name='My Robot')
        spec = robot.build_spec()
        assert spec.name == 'My Robot'

    def test_spec_robot_row(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.ROBOT)
        assert len(rows) == 1
        headers = [h for h, _ in rows[0].columns]
        values = {h: v for h, v in rows[0].columns}
        assert 'Hits' in headers
        assert values['Locomotion'] == 'Wheels'
        assert values['Size'] == '3'

    def test_spec_traits_row(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.TRAITS)
        assert len(rows) == 1

    def test_spec_programming_row(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.PROGRAMMING)
        assert len(rows) == 1
        assert rows[0].value == 'Primitive'

    def test_spec_endurance_row(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.ENDURANCE)
        assert len(rows) == 1
        assert 'hours' in rows[0].value

    def test_spec_attacks_row_empty(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.ATTACKS)
        assert rows[0].value == '—'

    def test_spec_attacks_row_with_attack(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot(attacks=['Claw (2D)'])
        rows = robot.build_spec().rows_for_section(RobotSpecSection.ATTACKS)
        assert rows[0].value == 'Claw (2D)'

    def test_spec_manipulators_row_empty(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot(manipulators=[])
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        assert rows[0].value == '—'

    def test_spec_manipulators_row_with_item(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot(manipulators=['Basic (STR 7)'])
        rows = robot.build_spec().rows_for_section(RobotSpecSection.MANIPULATORS)
        assert rows[0].value == 'Basic (STR 7)'

    def test_spec_skills_row_present(self):
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot()
        rows = robot.build_spec().rows_for_section(RobotSpecSection.SKILLS)
        assert len(rows) == 1

    def test_spec_skills_row_primitive_clean(self):
        from ceres.make.robot import PrimitiveBrain
        from ceres.make.robot.spec import RobotSpecSection

        robot = make_robot(brain=PrimitiveBrain(function='clean'))
        rows = robot.build_spec().rows_for_section(RobotSpecSection.SKILLS)
        assert 'Profession (domestic cleaner) 2' in rows[0].value

    def test_spec_skills_row_advanced_with_bandwidth(self):
        from ceres.make.robot import AdvancedBrain
        from ceres.make.robot.skills import SkillPackage
        from ceres.make.robot.spec import RobotSpecSection

        brain = AdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Electronics (remote ops)', level=1, bandwidth=1),),
        )
        robot = make_robot(brain=brain)
        rows = robot.build_spec().rows_for_section(RobotSpecSection.SKILLS)
        value = rows[0].value
        assert 'Electronics (remote ops) 1' in value
        assert '+1 Bandwidth available' in value


class TestSkillsDisplay:
    def test_no_brain_skills_no_options(self):
        robot = make_robot()
        assert robot.skills_display == '—'

    def test_primitive_clean_shows_skill(self):
        from ceres.make.robot import PrimitiveBrain

        robot = make_robot(brain=PrimitiveBrain(function='clean'))
        assert 'Profession (domestic cleaner) 2' in robot.skills_display

    def test_advanced_with_remaining_bandwidth(self):
        from ceres.make.robot import AdvancedBrain
        from ceres.make.robot.skills import SkillPackage

        brain = AdvancedBrain(
            brain_tl=12,
            installed_skills=(SkillPackage(name='Electronics (remote ops)', level=1, bandwidth=1),),
        )
        robot = make_robot(brain=brain)
        display = robot.skills_display
        assert 'Electronics (remote ops) 1' in display
        assert '+1 Bandwidth available' in display

    def test_option_skill_included(self):
        robot = make_robot(options=[_SkillPart()])
        assert 'Recon 1' in robot.skills_display

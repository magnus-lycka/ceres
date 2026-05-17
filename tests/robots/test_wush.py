# Source: user-supplied stat block (no refs/robot/xxx_wush.md).
#
# SIZE_2 TL15: STR = 2×2−1 = 3, DEX = ceil(15/2)+1 = 9. Source: 2× (STR 3 DEX 9). ✓
# PrimitiveBrain (clean, TL8): INT 1, programming 'Primitive (clean) (INT 1)'.
#   Source: 'Primitive (Clean), INT 1' — Ceres uses parentheses format consistent with BasicBrain. ✓
# WheelsAtvLocomotion base speed 5m (source: 5m). ✓
# Endurance: WheelsATV base 72h × TL15 multiplier 2.0 = 144h. ✓
# Armour: TL15 → base +4. Source: Armour (+4). ✓
# No IncreasedArmour, no ATV speed band enhancement.
#
# Default suite (5 slots): Visual Spectrum Sensor, Voder Speaker, Auditory Sensor,
#   Transceiver 5km (improved), Drone Interface. No Wireless Data Link. ✓
# DomesticCleaningEquipment(small): 1 slot, Cr100. ✓
# StorageCompartment(1 slot): 1 slot, Cr50. ✓
# Slots: available=2 (SIZE_2). Used=2 (cleaning 1 + storage 1). Remaining=0. ✓
#
# Cost: BCC(SIZE_2 × WheelsATV) = 200 × 3.0 = Cr600.
#   PrimitiveBrain = Cr100. DomesticCleaningEquipment small = Cr100. StorageCompartment = Cr50.
#   Total = Cr850 (exact match). ✓

from types import SimpleNamespace

from ceres.make.robot import Manipulator, PrimitiveBrain, Robot, RobotSize, WheelsAtvLocomotion, default_suite
from ceres.make.robot.options import DomesticCleaningEquipment, StorageCompartment
from ceres.make.robot.spec import RobotSpecSection
from ceres.make.robot.text import format_traits

_expected = SimpleNamespace(
    hits=4,
    locomotion='Wheels, ATV',
    speed='5m',
    tl=15,
    base_armour=4,
    traits='Armour (+4), ATV, Small (-3)',
    programming='Primitive (clean) (INT 1)',
    endurance_hours=144,
    attacks='—',
    manipulators='2× (STR 3 DEX 9)',
    available_slots=2,
    used_slots=2,
    remaining_slots=0,
    cost=850,
)


def build_wush() -> Robot:
    """Source: user-supplied stat block — Wush, SIZE_2 TL15 Wheels ATV, PrimitiveBrain (clean)."""
    return Robot(
        name='Wush',
        tl=15,
        size=RobotSize.SIZE_2,
        locomotion=WheelsAtvLocomotion(),
        brain=PrimitiveBrain(function='clean'),
        manipulators=[Manipulator(), Manipulator()],
        options=[
            *default_suite(
                see=True,
                speak=True,
                hear=True,
                wireless=False,
                improved_transceiver=True,
                drone=True,
            ),
            DomesticCleaningEquipment(size='small'),
            StorageCompartment(slots_count=1),
        ],
    )


class TestWush:
    def test_hits(self):
        assert build_wush().hits == _expected.hits

    def test_base_armour(self):
        assert build_wush().base_armour == _expected.base_armour

    def test_traits(self):
        assert format_traits(build_wush().traits) == _expected.traits

    def test_programming(self):
        assert build_wush().brain.programming_label() == _expected.programming

    def test_endurance(self):
        assert int(build_wush().base_endurance) == _expected.endurance_hours

    def test_cost(self):
        assert build_wush().total_cost == _expected.cost

    def test_locomotion_label(self):
        assert build_wush().locomotion.label() == _expected.locomotion

    def test_speed_label(self):
        assert build_wush().speed_label == _expected.speed

    def test_available_slots(self):
        assert build_wush().available_slots == _expected.available_slots

    def test_used_slots(self):
        assert build_wush().used_slots == _expected.used_slots

    def test_remaining_slots(self):
        assert build_wush().remaining_slots == _expected.remaining_slots

    def test_spec_attacks_row(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.ATTACKS)[0].value
        assert value == _expected.attacks

    def test_spec_manipulators_row(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.MANIPULATORS)[0].value
        assert value == _expected.manipulators

    def test_spec_options_has_visual_spectrum_sensor(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Visual Spectrum Sensor' in value

    def test_spec_options_has_auditory_sensor(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Auditory Sensor' in value

    def test_spec_options_has_voder_speaker(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Voder Speaker' in value

    def test_spec_options_has_drone_interface(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Drone Interface' in value

    def test_spec_options_has_transceiver_5km_improved(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Transceiver 5km (improved)' in value

    def test_spec_options_has_domestic_cleaning_equipment(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Domestic Cleaning Equipment (small)' in value

    def test_spec_options_has_storage_compartment(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Storage Compartment (1 Slots)' in value

    def test_no_wireless_data_link_in_options(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Wireless Data Link' not in value

    def test_no_spare_slots_in_options(self):
        spec = build_wush().build_spec()
        value = spec.rows_for_section(RobotSpecSection.OPTIONS)[0].value
        assert 'Spare Slots' not in value

    def test_profession_domestic_cleaner_2(self):
        robot = build_wush()
        assert 'Profession (domestic cleaner) 2' in robot.skills_display

    def test_manipulator_str_3(self):
        robot = build_wush()
        m = robot.manipulators[0]
        assert m.effective_str(RobotSize.SIZE_2) == 3

    def test_manipulator_dex_9(self):
        robot = build_wush()
        m = robot.manipulators[0]
        assert m.effective_dex(15) == 9

    def test_json_roundtrip(self):
        robot = build_wush()
        restored = Robot.model_validate_json(robot.model_dump_json())
        assert restored.name == 'Wush'
        assert restored.tl == _expected.tl
        assert restored.size == RobotSize.SIZE_2
        assert isinstance(restored.locomotion, WheelsAtvLocomotion)
        assert isinstance(restored.brain, PrimitiveBrain)
        assert restored.brain.function == 'clean'

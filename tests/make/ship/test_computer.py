from pydantic import TypeAdapter
import pytest

from ceres.gear.software import Intellect
from ceres.make.ship.base import ShipBase
from ceres.make.ship.computer import (
    Computer,
    Computer5,
    Computer10,
    Computer15,
    Core40,
    Core50,
)
from ceres.make.ship.software import Library, Manoeuvre


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_computer_5_cost():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert c.tl == 7
    assert c.assembly_tl == 12
    assert c.processing == 5
    assert c.can_run_jump_control(5)
    assert not c.can_run_jump_control(10)
    assert float(c.cost) == 30_000


def test_computer_10_cost():
    c = Computer10()
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 160_000


def test_computer_15_cost():
    c = Computer15()
    c.bind(DummyOwner(12, 6))
    assert float(c.cost) == 2_000_000


def test_computer_rejects_invalid_processing():
    with pytest.raises(ValueError, match='computer_23'):
        TypeAdapter(Computer).validate_python({'kind': 'computer_23'})


def test_computer_tons_zero():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert float(c.tons) == 0


def test_computer_power_zero():
    c = Computer5()
    c.bind(DummyOwner(12, 6))
    assert c.power == 0


def test_computer_5_min_tl():
    c = Computer5()
    c.bind(DummyOwner(6, 100))
    assert 'Requires TL7, ship is TL6' in c.notes.errors


def test_computer_recomputes_cost_from_input():
    c = TypeAdapter(Computer).validate_python({'kind': 'computer_5', 'cost': 999})
    c.bind(DummyOwner(12, 6))
    assert c.cost == 30_000


def test_computer_values_are_computed_properties_not_serialized_fields():
    c = TypeAdapter(Computer).validate_python({'kind': 'computer_5', 'tons': 999, 'cost': 999, 'power': 999})
    c.bind(DummyOwner(12, 6))
    dump = c.model_dump()

    assert c.tons == pytest.approx(0.0)
    assert c.cost == pytest.approx(30_000.0)
    assert c.power == pytest.approx(0.0)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_computer_bis_increases_cost_and_jump_control_capacity():
    c = Computer5(bis=True)
    c.bind(DummyOwner(12, 6))
    assert c.processing == 5
    assert c.can_run_jump_control(10)
    assert not c.can_run_jump_control(15)
    assert c.cost == 45_000


def test_computer_fib_increases_cost():
    c = Computer5(fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 45_000


def test_computer_bis_and_fib_double_cost():
    c = Computer5(bis=True, fib=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == 60_000


def test_core_40_hardware():
    c = Core40()
    c.bind(DummyOwner(12, 100))
    assert c.tl == 9
    assert c.processing == 40
    assert c.can_run_jump_control(100)
    assert c.cost == 45_000_000


def test_core_40_fib_hardware():
    c = Core40(fib=True)
    c.bind(DummyOwner(13, 100))
    assert c.build_item() == 'Core/40/fib'
    assert c.cost == pytest.approx(67_500_000.0)


def test_core_values_are_computed_properties_not_serialized_fields():
    c = Core40.model_validate({'tons': 999, 'cost': 999, 'power': 999})
    c.bind(DummyOwner(12, 100))
    dump = c.model_dump()

    assert c.tons == pytest.approx(0.0)
    assert c.cost == pytest.approx(45_000_000.0)
    assert c.power == pytest.approx(0.0)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_included_software_packages():
    c = Computer5()
    c.bind(DummyOwner(12, 100))
    assert [type(package) for package in c.included_software] == [Library, Manoeuvre, Intellect]
    assert [package.cost for package in c.included_software] == [0.0, 0.0, 0.0]


def test_computer5_retro_1_level_halves_base_cost():
    c = Computer5(retro_levels=1)
    assert c.base_cost == 15_000.0


def test_computer5_retro_2_levels_quarters_base_cost():
    c = Computer5(retro_levels=2)
    assert c.base_cost == 7_500.0


def test_core40_retro_1_level_halves_base_cost():
    c = Core40(retro_levels=1)
    assert c.base_cost == 22_500_000.0


def test_computer10_proto_1_level_multiplies_base_cost_by_10():
    c = Computer10(proto_levels=1)
    assert c.base_cost == 1_600_000.0


def test_computer10_proto_2_levels_multiplies_base_cost_by_100():
    c = Computer10(proto_levels=2)
    assert c.base_cost == 16_000_000.0


def test_computer_proto_3_levels_raises():
    with pytest.raises(ValueError, match='Proto tech not available for 3 TLs'):
        Computer10(proto_levels=3)


def test_computer_retro_and_proto_raises():
    with pytest.raises(ValueError, match='Cannot have both retro_levels and proto_levels'):
        Computer10(retro_levels=1, proto_levels=1)


def test_computer5_retro_bis_applies_bis_on_retro_base():
    c = Computer5(retro_levels=1, bis=True)
    c.bind(DummyOwner(12, 6))
    assert c.cost == pytest.approx(22_500.0)  # 15_000 * 1.5


def test_core50_retro_fib_applies_fib_on_retro_base():
    c = Core50(retro_levels=2, fib=True)
    c.bind(DummyOwner(14, 100))
    assert c.cost == pytest.approx(60_000_000.0 / 4 * 1.5)


def test_computer15_proto_1_lowers_effective_tl():
    c = Computer15(proto_levels=1)
    c.bind(DummyOwner(10, 100))
    assert not any('Requires TL' in e for e in c.notes.errors)


def test_computer15_proto_1_fails_one_below_effective_tl():
    c = Computer15(proto_levels=1)
    c.bind(DummyOwner(9, 100))
    assert any('Requires TL10' in e for e in c.notes.errors)


def test_computer10_retro_3_in_tl11_ship_fails_retro_check():
    # retro_levels=3 needs ship TL >= 9+3=12; TL11 is insufficient
    c = Computer10(retro_levels=3)
    c.bind(DummyOwner(11, 100))
    assert any('Retro/3 requires ship TL12' in e for e in c.notes.errors)


def test_computer10_retro_2_in_tl11_ship_passes_retro_check():
    # retro_levels=2 needs ship TL >= 9+2=11; TL11 is exactly sufficient
    c = Computer10(retro_levels=2)
    c.bind(DummyOwner(11, 100))
    assert not any('Retro' in e for e in c.notes.errors)


def test_retro_computer_info_note_shows_software_tl_cap():
    c = Computer10(retro_levels=2)
    c.bind(DummyOwner(11, 100))
    assert any('Software limited to TL9' in msg for msg in c.notes.infos)


def test_prototype_computer_has_0_1_ton():
    c = Computer15(proto_levels=1)
    assert c.tons == pytest.approx(0.1)


def test_early_prototype_computer_has_1_ton():
    c = Computer15(proto_levels=2)
    assert c.tons == pytest.approx(1.0)


def test_standard_computer_has_zero_tons():
    c = Computer15()
    assert c.tons == pytest.approx(0.0)


def test_prototype_computer_warns_skill_dm_minus_1():
    c = Computer15(proto_levels=1)
    assert any('Skill DM -1' in msg for msg in c.notes.warnings)


def test_prototype_computer_warns_quirk():
    c = Computer15(proto_levels=1)
    assert any('Quirk' in msg for msg in c.notes.warnings)


def test_early_prototype_computer_warns_skill_dm_minus_2():
    c = Computer15(proto_levels=2)
    assert any('Skill DM -2' in msg for msg in c.notes.warnings)


def test_early_prototype_computer_warns_unreliable():
    c = Computer15(proto_levels=2)
    assert any('Unreliable' in msg for msg in c.notes.warnings)


def test_early_prototype_computer_warns_2_quirks():
    c = Computer15(proto_levels=2)
    assert any('2+ Quirks' in msg for msg in c.notes.warnings)


def test_standard_computer_has_no_proto_warnings():
    c = Computer15()
    assert not c.notes.warnings

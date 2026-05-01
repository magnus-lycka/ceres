import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.drives import (
    DecreasedFuel,
    DriveSection,
    EmergencyPowerSystem,
    FusionPlantTL8,
    FusionPlantTL12,
    FusionPlantTL15,
    JDrive,
    LimitedRange,
    MDrive,
    PowerSection,
    RDrive,
)
from ceres.make.ship.parts import Advanced, Budget, IncreasedSize, SizeReduction, VeryAdvanced
from ceres.make.ship.storage import FuelSection, JumpFuel, OperationFuel, ReactionFuel


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement, **kwargs):
        super().__init__(tl=tl, displacement=displacement, **kwargs)


# --- JDrive ---


@pytest.mark.parametrize('level, tl, pct', [
    (1, 9, 0.025),
    (2, 11, 0.05),
    (3, 12, 0.075),
    (4, 13, 0.10),
    (5, 14, 0.125),
    (6, 15, 0.15),
    (7, 16, 0.175),
    (8, 17, 0.20),
    (9, 18, 0.225),
])
def test_jdrive_tons_cost_tl(level, tl, pct):
    d = JDrive(level)
    d.bind(DummyOwner(tl, 200))
    expected_tons = 200 * pct + 5
    assert d.tl == tl
    assert d.level == level
    assert float(d.tons) == pytest.approx(expected_tons)
    assert float(d.cost) == pytest.approx(expected_tons * 1_500_000)


def test_jdrive_with_decreased_fuel_x2_changes_cost_and_required_tl():
    d = JDrive(2, customisation=VeryAdvanced(DecreasedFuel, DecreasedFuel))
    d.bind(DummyOwner(15, 450))
    assert d.tl == 11
    assert float(d.tons) == pytest.approx(27.5)
    assert float(d.cost) == pytest.approx(51_562_500.0)
    assert float(d.power) == pytest.approx(90.0)


def test_jump_fuel_respects_decreased_fuel_additively():
    my_ship = ship.Ship(
        tl=15,
        displacement=450,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(j_drive=JDrive(2, customisation=VeryAdvanced(DecreasedFuel, DecreasedFuel))),
        fuel=FuelSection(jump_fuel=JumpFuel(parsecs=2)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.jump_fuel is not None
    assert my_ship.fuel.jump_fuel.tons == pytest.approx(81.0)


def test_jump_drive_uses_performance_displacement_when_transporting_external_load():
    d = JDrive(2)
    d.bind(DummyOwner(12, 400, maintained_external_displacement=40))
    assert d.build_item() == 'Jump 2 (440t)'
    assert float(d.tons) == pytest.approx(27.0)
    assert float(d.cost) == pytest.approx(40_500_000.0)
    assert float(d.power) == pytest.approx(88.0)


# --- MDrive ---


def test_mdrive_standard_tons():
    d = MDrive(6)
    d.bind(DummyOwner(12, 6))
    assert d.tl == 12
    assert d.ship_tl == 12
    assert float(d.tons) == pytest.approx(0.36)


def test_mdrive_uses_performance_displacement_when_transporting_external_load():
    d = MDrive(2)
    d.bind(DummyOwner(12, 400, maintained_external_displacement=40))
    assert d.build_item() == 'M-Drive 2 (440t)'
    assert float(d.tons) == pytest.approx(8.8)
    assert float(d.cost) == pytest.approx(17_600_000.0)
    assert float(d.power) == pytest.approx(88.0)


def test_mdrive_standard_cost():
    d = MDrive(6)
    d.bind(DummyOwner(12, 6))
    assert float(d.cost) == pytest.approx(720_000)


def test_mdrive_power():
    d = MDrive(6)
    d.bind(DummyOwner(12, 6))
    assert d.power == 4  # ceil(0.1 * 6 * 6) = ceil(3.6) = 4


def test_mdrive_thrust_zero_uses_station_power_rule():
    d = MDrive(0)
    d.bind(DummyOwner(12, 10_000))
    assert d.tons == pytest.approx(50.0)
    assert d.cost == pytest.approx(100_000_000.0)
    assert d.power == pytest.approx(250.0)


def test_budget_increased_size_mdrive_values():
    d = MDrive(7, customisation=Budget(IncreasedSize))
    d.bind(DummyOwner(13, 400))
    assert d.build_item() == 'M-Drive 7'
    assert float(d.tons) == pytest.approx(35.0)
    assert float(d.cost) == pytest.approx(42_000_000.0)


def test_limited_range_is_drive_specific_customisation():
    assert [(note.category.value, note.message) for note in LimitedRange.build_notes()] == [
        ('info', 'This manoeuvre drive only functions within the 100-diameter limit'),
    ]


def test_drive_section_all_parts():
    drives = DriveSection(m_drive=MDrive(6), r_drive=RDrive(3), j_drive=JDrive(2))
    assert drives._all_parts() == [drives.m_drive, drives.r_drive, drives.j_drive]


def test_power_section_all_parts():
    power = PowerSection(fusion_plant=FusionPlantTL12(output=8))
    assert power._all_parts() == [power.fusion_plant]



def test_mdrive_tl_too_low():
    d = MDrive(6)
    d.bind(DummyOwner(11, 6))
    assert ('error', 'Requires TL12, ship is TL11') in [
        (note.category.value, note.message) for note in d.notes
    ]


def test_mdrive_recomputes_cost_from_input():
    d = MDrive.model_validate({'level': 6, 'cost': 999})
    d.bind(DummyOwner(12, 6))
    assert d.cost == pytest.approx(720_000)


def test_mdrive_recomputes_tons_from_input():
    d = MDrive.model_validate({'level': 6, 'tons': 999})
    d.bind(DummyOwner(12, 6))
    assert d.tons == pytest.approx(0.36)


# --- FusionPlant ---


def test_fusion_plant_base_tons():
    p = FusionPlantTL12(output=8)
    p.bind(DummyOwner(12, 6))
    assert p.tl == 12
    assert p.ship_tl == 12
    assert float(p.tons) == pytest.approx(8 / 15)


def test_fusion_plant_base_cost():
    p = FusionPlantTL12(output=8)
    p.bind(DummyOwner(12, 6))
    assert float(p.cost) == pytest.approx(8 / 15 * 1_000_000)


def test_fusion_plant_output():
    p = FusionPlantTL12(output=8)
    assert p.output == 8


def test_fusion_plant_power_zero():
    # Power plant generates power; it does not consume it
    p = FusionPlantTL12(output=8)
    p.bind(DummyOwner(12, 6))
    assert p.power == 0



def test_fusion_plant_recomputes_tons_from_input():
    p = FusionPlantTL12.model_validate({'output': 8, 'tons': 999})
    p.bind(DummyOwner(12, 6))
    assert p.tons == pytest.approx(8 / 15)


def test_fusion_plant_tl8_variant():
    p = FusionPlantTL8(output=8)
    p.bind(DummyOwner(12, 6))
    assert p.tl == 8
    assert float(p.tons) == pytest.approx(0.8)
    assert float(p.cost) == pytest.approx(400_000)


def test_fusion_plant_tl15_variant():
    p = FusionPlantTL15(output=8)
    p.bind(DummyOwner(15, 6))
    assert p.tl == 15
    assert float(p.tons) == pytest.approx(0.4)
    assert float(p.cost) == pytest.approx(800_000)


def test_budget_increased_size_fusion_plant_values():
    p = FusionPlantTL12(output=482, customisation=Budget(IncreasedSize))
    p.bind(DummyOwner(13, 400))
    assert p.build_item() == 'Fusion (TL 12), Power 482'
    assert float(p.tons) == pytest.approx(40.1666666667)
    assert float(p.cost) == pytest.approx(24_100_000.0)


def test_size_reduced_fusion_plant_values():
    p = FusionPlantTL12(output=436, customisation=Advanced(SizeReduction))
    p.bind(DummyOwner(13, 400))
    assert p.build_item() == 'Fusion (TL 12), Power 436'
    assert float(p.tons) == pytest.approx(26.16)
    assert float(p.cost) == pytest.approx(31_973_333.3333)


def test_emergency_power_system_values():
    my_ship = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(
            fusion_plant=FusionPlantTL12(output=436, customisation=Advanced(SizeReduction)),
            emergency_power_system=EmergencyPowerSystem.from_fusion_plant(
                FusionPlantTL12(output=436, customisation=Advanced(SizeReduction))
            ),
        ),
    )
    assert my_ship.power is not None
    eps = my_ship.power.emergency_power_system
    assert eps is not None
    assert eps.tons == pytest.approx(2.616)
    assert eps.cost == pytest.approx(3_197_333.3333)


def test_fusion_plant_rejects_ship_below_tl():
    plant = FusionPlantTL12(output=8)
    plant.bind(DummyOwner(11, 6))
    assert ('error', 'Requires TL12, ship is TL11') in [
        (note.category.value, note.message) for note in plant.notes
    ]


def _make_ship_with_plant():
    fuel = OperationFuel(weeks=1)
    s = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        power=PowerSection(fusion_plant=FusionPlantTL12(output=8)),
        fuel=FuelSection(operation_fuel=fuel),
    )
    assert s.fuel is not None
    return s, s.fuel.operation_fuel


def test_operation_fuel_1_week_tons():
    # Small craft round operation fuel up to tenths of a dTon.
    _, fuel = _make_ship_with_plant()
    assert float(fuel.tons) == pytest.approx(0.1)


def test_operation_fuel_cost_zero():
    _, fuel = _make_ship_with_plant()
    assert fuel.cost == 0


def test_operation_fuel_power_zero():
    _, fuel = _make_ship_with_plant()
    assert fuel.power == 0


def test_operation_fuel_requires_plant():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        fuel=FuelSection(operation_fuel=OperationFuel(weeks=1)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.operation_fuel is not None
    assert my_ship.fuel.operation_fuel.tons == 0.0
    assert ('error', 'Ship must have a FusionPlant to compute OperationFuel') in [
        (note.category.value, note.message) for note in my_ship.fuel.operation_fuel.notes
    ]


def test_rdrive_tons_cost_and_power():
    d = RDrive(16)
    d.bind(DummyOwner(12, 6))
    assert d.tl == 12
    assert d.bulkhead_label() == 'R-Drive'
    assert d.tons == pytest.approx(1.92)
    assert d.cost == pytest.approx(384_000)
    assert d.power == 0.0


def test_rdrive_unsupported_level_errors():
    d = RDrive(99)
    with pytest.raises(KeyError):
        d.bind(DummyOwner(12, 6))
    assert ('error', 'Unsupported reaction drive level 99') in [
        (note.category.value, note.message) for note in d.notes
    ]


def test_rdrive_tl_too_low():
    d = RDrive(16)
    d.bind(DummyOwner(11, 6))
    assert ('error', 'Requires TL12, ship is TL11') in [
        (note.category.value, note.message) for note in d.notes
    ]


def test_reaction_fuel_minutes_of_operation():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(r_drive=RDrive(16)),
        fuel=FuelSection(reaction_fuel=ReactionFuel(minutes=52)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.reaction_fuel is not None
    assert my_ship.fuel.reaction_fuel.tons == pytest.approx(2.08)


def test_size_reduced_fusion_plant_item_includes_output_but_not_customisation_label():
    p = FusionPlantTL12(output=436, customisation=Advanced(SizeReduction))
    p.bind(DummyOwner(13, 400))
    assert p.build_item() == 'Fusion (TL 12), Power 436'


def test_size_reduced_fusion_plant_has_customisation_note():
    p = FusionPlantTL12(output=436, customisation=Advanced(SizeReduction))
    p.bind(DummyOwner(13, 400))
    info_notes = [n.message for n in p.notes if n.category.value == 'info']
    assert 'Advanced: Size Reduction' in info_notes


def test_budget_increased_size_mdrive_item_is_base_name_only():
    p = MDrive(1, customisation=Budget(IncreasedSize))
    p.bind(DummyOwner(12, 100))
    assert p.build_item() == 'M-Drive 1'


def test_budget_increased_size_mdrive_has_customisation_note():
    p = MDrive(1, customisation=Budget(IncreasedSize))
    p.bind(DummyOwner(12, 100))
    info_notes = [n.message for n in p.notes if n.category.value == 'info']
    assert 'Budget: Increased Size' in info_notes


def test_mdrive_unsupported_level_errors():
    d = MDrive(99)
    with pytest.raises(KeyError):
        d.bind(DummyOwner(15, 100))
    assert ('error', 'Unsupported M-Drive level 99') in [
        (note.category.value, note.message) for note in d.notes
    ]


def test_jdrive_build_item_parsecs_and_bulkhead_label():
    d = JDrive(2)
    d.bind(DummyOwner(11, 200))
    assert d.build_item() == 'Jump 2'
    assert d.parsecs == 2
    assert d.bulkhead_label() == 'Jump Drive'


def test_jdrive_unsupported_level_errors():
    d = JDrive(99)
    with pytest.raises(KeyError):
        d.bind(DummyOwner(18, 200))
    assert ('error', 'Unsupported J-Drive level 99') in [
        (note.category.value, note.message) for note in d.notes
    ]


def test_jdrive_tl_too_low():
    d = JDrive(2)
    d.bind(DummyOwner(10, 200))
    assert ('error', 'Requires TL11, ship is TL10') in [
        (note.category.value, note.message) for note in d.notes
    ]


def test_emergency_power_system_requires_fusion_plant():
    with pytest.raises(RuntimeError, match='EmergencyPowerSystem requires a fusion plant'):
        ship.Ship(
            tl=13,
            displacement=400,
            hull=hull.Hull(configuration=hull.standard_hull),
            power=PowerSection(emergency_power_system=EmergencyPowerSystem()),
        )


def test_power_section_adds_emergency_power_system_spec_row():
    my_ship = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(
            fusion_plant=FusionPlantTL12(output=436, customisation=Advanced(SizeReduction)),
            emergency_power_system=EmergencyPowerSystem(),
        ),
    )
    spec = my_ship.build_spec()
    row = spec.row('Emergency Power System', section='Power')
    assert row.tons == pytest.approx(2.616)
    assert row.cost == pytest.approx(3_197_333.3333)

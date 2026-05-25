from pydantic import TypeAdapter
import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.crafts import CraftSection, DockingClamp, SpaceCraft
from ceres.make.ship.drives import (
    DecreasedFuel,
    DriveSection,
    EarlyJump,
    EmergencyPowerSystem,
    FuelEfficient,
    FuelInefficient,
    FusionPlantTL8,
    FusionPlantTL12,
    FusionPlantTL15,
    JDrive,
    JDrive1,
    JDrive2,
    JDrive3,
    JDrive4,
    JDrive5,
    JDrive6,
    JDrive7,
    JDrive8,
    JDrive9,
    JumpEnergyInefficient,
    LateJump,
    LimitedRange,
    MDrive,
    MDrive0,
    MDrive1,
    MDrive2,
    MDrive5,
    MDrive6,
    MDrive7,
    PowerSection,
    RDrive,
    RDrive3,
    RDrive16,
    SolarSail,
    SpinExtPlasmaDrive,
    SpinExtPlasmaDriveEnergyEfficient,
    SpinExtPlasmaDriveEnergyInefficient,
    SpinExtPlasmaDriveFuelEfficient,
    SpinExtPlasmaDriveFuelInefficient,
    SpinExtPlasmaDriveIncreasedSize,
    SpinExtPlasmaDriveSizeReduction,
    SpinExtSolarSailTL6,
    SpinExtSolarSailTL8,
    SpinExtSolarSailTL12,
    StealthJump,
)
from ceres.make.ship.parts import Advanced, Budget, IncreasedSize, SizeReduction, VeryAdvanced
from ceres.make.ship.storage import FuelSection, JumpFuel, OperationFuel, ReactionFuel
from ceres.shared import NoteList


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement, **kwargs):
        super().__init__(tl=tl, displacement=displacement, **kwargs)


# --- JDrive ---


@pytest.mark.parametrize(
    'drive_cls, level, tl, pct',
    [
        (JDrive1, 1, 9, 0.025),
        (JDrive2, 2, 11, 0.05),
        (JDrive3, 3, 12, 0.075),
        (JDrive4, 4, 13, 0.10),
        (JDrive5, 5, 14, 0.125),
        (JDrive6, 6, 15, 0.15),
        (JDrive7, 7, 16, 0.175),
        (JDrive8, 8, 17, 0.20),
        (JDrive9, 9, 18, 0.225),
    ],
)
def test_jdrive_tons_cost_tl(drive_cls, level, tl, pct):
    d = drive_cls()
    d.bind(DummyOwner(tl, 200))
    expected_tons = 200 * pct + 5
    assert d.tl == tl
    assert d.level == level
    assert float(d.tons) == pytest.approx(expected_tons)
    assert float(d.cost) == pytest.approx(expected_tons * 1_500_000)


def test_jdrive_with_decreased_fuel_x2_changes_cost_and_required_tl():
    d = JDrive2(customisation=VeryAdvanced(modifications=[DecreasedFuel, DecreasedFuel]))
    d.bind(DummyOwner(15, 450))
    assert d.tl == 11
    assert float(d.tons) == pytest.approx(27.5)
    assert float(d.cost) == pytest.approx(51_562_500.0)
    assert float(d.power) == pytest.approx(90.0)


def test_jdrive_with_early_jump_is_allowed_and_noted():
    d = JDrive2(customisation=Advanced(modifications=[EarlyJump]))
    d.bind(DummyOwner(12, 200))

    assert 'Modification not allowed for JDrive2: Early Jump' not in d.notes.errors
    assert 'Advanced: Early Jump' in d.notes.infos
    assert 'Can jump at the 90-diameter limit' in d.notes.infos


def test_jdrive_with_stealth_jump_is_allowed_and_noted():
    d = JDrive2(customisation=VeryAdvanced(modifications=[StealthJump]))
    d.bind(DummyOwner(13, 200))

    assert 'Modification not allowed for JDrive2: Stealth Jump' not in d.notes.errors
    assert 'Very Advanced: Stealth Jump' in d.notes.infos
    assert 'Reduces jump emergence radiation signature' in d.notes.infos


def test_jdrive_with_late_jump_is_allowed_and_noted():
    d = JDrive2(customisation=Budget(modifications=[LateJump]))
    d.bind(DummyOwner(11, 200))

    assert 'Modification not allowed for JDrive2: Late Jump' not in d.notes.errors
    assert 'Budget: Late Jump' in d.notes.infos
    assert 'Requires the 150-diameter limit before jumping' in d.notes.infos


def test_jdrive_energy_inefficient_uses_jump_drive_power_rule():
    d = JDrive2(customisation=Budget(modifications=[JumpEnergyInefficient]))
    d.bind(DummyOwner(11, 200))

    assert 'Modification not allowed for JDrive2: Energy Inefficient' not in d.notes.errors
    assert d.power == pytest.approx(52.0)
    assert 'Budget: Energy Inefficient' in d.notes.infos


def test_jdrive_values_are_computed_properties_not_serialized_fields():
    d = JDrive2.model_validate({'tons': 999, 'cost': 999, 'power': 999})
    d.bind(DummyOwner(12, 200))
    assert d.tons == pytest.approx(15.0)
    assert d.cost == pytest.approx(22_500_000.0)
    assert d.power == pytest.approx(40.0)
    dump = d.model_dump()
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_jump_fuel_respects_decreased_fuel_additively():
    my_ship = ship.Ship(
        tl=15,
        displacement=450,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(j_drive=JDrive2(customisation=VeryAdvanced(modifications=[DecreasedFuel, DecreasedFuel]))),
        fuel=FuelSection(jump_fuel=JumpFuel(parsecs=2)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.jump_fuel is not None
    assert my_ship.fuel.jump_fuel.tons == pytest.approx(81.0)


def test_jump_drive_uses_performance_displacement_when_transporting_external_load():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.dispersed_structure),
        drives=DriveSection(j_drive=JDrive2()),
        craft=CraftSection(docking_clamps=[DockingClamp(craft=SpaceCraft.from_catalog('Pinnace'), transported=True)]),
    )
    assert my_ship.drives is not None
    assert my_ship.drives.j_drive is not None
    assert my_ship.drives.j_drive.build_item() == 'Jump 2 (440t)'
    assert float(my_ship.drives.j_drive.tons) == pytest.approx(27.0)
    assert float(my_ship.drives.j_drive.cost) == pytest.approx(40_500_000.0)
    assert float(my_ship.drives.j_drive.power) == pytest.approx(88.0)


# --- MDrive ---


def test_mdrive_standard_tons():
    d = MDrive6()
    d.bind(DummyOwner(12, 6))
    assert d.tl == 12
    assert d.assembly_tl == 12
    assert float(d.tons) == pytest.approx(0.36)


def test_mdrive_uses_performance_displacement_when_transporting_external_load():
    my_ship = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.dispersed_structure),
        drives=DriveSection(m_drive=MDrive2()),
        craft=CraftSection(docking_clamps=[DockingClamp(craft=SpaceCraft.from_catalog('Pinnace'), transported=True)]),
    )
    assert my_ship.drives is not None
    assert my_ship.drives.m_drive is not None
    assert my_ship.drives.m_drive.build_item() == 'M-Drive 2 (440t)'
    assert float(my_ship.drives.m_drive.tons) == pytest.approx(8.8)
    assert float(my_ship.drives.m_drive.cost) == pytest.approx(17_600_000.0)
    assert float(my_ship.drives.m_drive.power) == pytest.approx(88.0)


def test_mdrive_standard_cost():
    d = MDrive6()
    d.bind(DummyOwner(12, 6))
    assert float(d.cost) == pytest.approx(720_000)


def test_mdrive_power():
    d = MDrive6()
    d.bind(DummyOwner(12, 6))
    assert d.power == 4  # ceil(0.1 * 6 * 6) = ceil(3.6) = 4


def test_mdrive_thrust_zero_uses_station_power_rule():
    d = MDrive0()
    d.bind(DummyOwner(12, 10_000))
    assert d.tons == pytest.approx(50.0)
    assert d.cost == pytest.approx(100_000_000.0)
    assert d.power == pytest.approx(250.0)


def test_concealed_mdrive_adds_tons_and_cost_but_not_power():
    d = MDrive6(concealed=True)
    d.bind(DummyOwner(12, 100))
    assert d.tons == pytest.approx(7.5)
    assert d.cost == pytest.approx(15_000_000.0)
    assert d.power == pytest.approx(60.0)


def test_concealed_mdrive_halves_effective_thrust_rounding_down():
    d = MDrive5(concealed=True)
    d.bind(DummyOwner(12, 100))
    assert d.effective_thrust == 2
    assert d.notes.infos == [
        'Concealed manoeuvre drive: effective Thrust 2',
        'Concealed manoeuvre drive must be within 3 metres of the accelerating surface',
        'Removing the outer bulkhead does not improve concealed manoeuvre drive performance',
    ]


def test_concealed_mdrive_roundtrips_through_mdrive_union():
    restored = TypeAdapter(MDrive).validate_python(MDrive6(concealed=True).model_dump())
    assert restored.concealed is True


def test_budget_increased_size_mdrive_values():
    d = MDrive7(customisation=Budget(modifications=[IncreasedSize]))
    d.bind(DummyOwner(13, 400))
    assert d.build_item() == 'M-Drive 7'
    assert float(d.tons) == pytest.approx(35.0)
    assert float(d.cost) == pytest.approx(42_000_000.0)


def test_limited_range_is_drive_specific_customisation():
    assert NoteList(LimitedRange.build_notes()).infos == [
        'This manoeuvre drive only functions within the 100-diameter limit'
    ]


def test_drive_section_all_parts():
    drives = DriveSection(m_drive=MDrive6(), r_drive=RDrive3(), j_drive=JDrive2())
    assert drives._all_parts() == [drives.m_drive, drives.r_drive, drives.j_drive]


def test_solar_sail_values_and_notes():
    sail = SolarSail()
    sail.bind(DummyOwner(9, 200))

    assert sail.tons == pytest.approx(10.0)
    assert sail.cost == pytest.approx(2_000_000.0)
    assert sail.power == 0.0
    assert sail.build_item() == 'Solar Sail'
    assert 'Effective Thrust 0 while using the solar sail as primary propulsion' in sail.notes.infos
    assert 'Requires several days to change course or speed' in sail.notes.infos
    assert 'Jump drives cannot be engaged while the solar sail is deployed' in sail.notes.infos


def test_solar_sail_appears_in_propulsion_spec_rows():
    my_ship = ship.Ship(
        tl=9,
        displacement=200,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(solar_sail=SolarSail()),
    )

    row = my_ship.build_spec().row('Solar Sail', section='Propulsion')

    assert row.tons == pytest.approx(10.0)
    assert row.cost == pytest.approx(2_000_000.0)
    assert row.power is None


def test_spinext_plasma_drive_values_and_notes():
    plasma = SpinExtPlasmaDrive(thrust=0.5)
    plasma.bind(DummyOwner(8, 100))

    assert plasma.tl == 8
    assert plasma.tons == pytest.approx(10.0)
    assert plasma.cost == pytest.approx(4_000_000.0)
    assert plasma.power == pytest.approx(10.0)
    assert plasma.fuel_tons_per_hour == pytest.approx(0.5)
    assert plasma.build_item() == 'SpinExt Plasma Drive, Thrust 0.5'
    assert 'Uses standard liquid hydrogen fuel' in plasma.notes.infos
    assert 'Consumes 0.5 tons of fuel per hour' in plasma.notes.infos
    assert 'Does not require or benefit from a gravity field, so it works in deep space' in plasma.notes.infos


def test_spinext_plasma_drive_modifications_apply_to_their_own_values():
    plasma = SpinExtPlasmaDrive(
        thrust=0.5,
        modifications=[
            SpinExtPlasmaDriveEnergyEfficient,
            SpinExtPlasmaDriveEnergyInefficient,
            SpinExtPlasmaDriveFuelEfficient,
            SpinExtPlasmaDriveFuelInefficient,
            SpinExtPlasmaDriveSizeReduction,
            SpinExtPlasmaDriveIncreasedSize,
        ],
    )
    plasma.bind(DummyOwner(8, 100))

    assert plasma.tons == pytest.approx(10.0 * 1.15)
    assert plasma.cost == pytest.approx(plasma.tons * 400_000)
    assert plasma.power == pytest.approx(plasma.tons * 0.80 * 1.30)
    assert plasma.fuel_tons_per_hour == pytest.approx(0.5 * 1.05)
    assert plasma.build_item() == (
        'SpinExt Plasma Drive, Thrust 0.5 '
        '(Energy Efficient, Energy Inefficient, Fuel Efficient, Fuel Inefficient, '
        'Size Reduction, Increased Size)'
    )
    assert 'Energy Efficient: consumes 20% less Power' in plasma.notes.infos
    assert 'Increased Size: uses 25% more tonnage' in plasma.notes.infos


def test_spinext_plasma_drive_appears_in_propulsion_spec_rows():
    my_ship = ship.Ship(
        tl=8,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(plasma_drive=SpinExtPlasmaDrive(thrust=0.5)),
    )

    row = my_ship.build_spec().row('SpinExt Plasma Drive, Thrust 0.5', section='Propulsion')

    assert row.tons == pytest.approx(10.0)
    assert row.cost == pytest.approx(4_000_000.0)
    assert row.power == pytest.approx(-10.0)


def test_spinext_tl8_solar_sail_values_and_notes():
    sail = SpinExtSolarSailTL8(tons=10)
    sail.bind(DummyOwner(8, 100))

    assert sail.cost == pytest.approx(4_000_000.0)
    assert sail.power == 0.0
    assert sail.effective_thrust == pytest.approx(0.01)
    assert sail.output == pytest.approx(0.0)
    assert sail.build_item() == 'SpinExt Solar Sail (TL 8), Thrust 0.01'
    assert 'Solar sail thrust assumes operation in a star habitable zone' in sail.notes.infos
    assert 'Solar sails require 1D × 10 rounds to deploy or retract' in sail.notes.infos
    assert 'Ships cannot jump with solar sails deployed' in sail.notes.infos
    assert 'Ships cannot use any other manoeuvre drive while solar sails are deployed' in sail.notes.infos


def test_spinext_solar_sail_table_values():
    tl6 = SpinExtSolarSailTL6(tons=10)
    tl8 = SpinExtSolarSailTL8(tons=10)
    tl12 = SpinExtSolarSailTL12(tons=10)
    for sail in [tl6, tl8, tl12]:
        sail.bind(DummyOwner(sail.tl, 100))

    assert tl6.effective_thrust == pytest.approx(0.005)
    assert tl6.cost == pytest.approx(2_000_000)
    assert tl8.effective_thrust == pytest.approx(0.01)
    assert tl8.cost == pytest.approx(4_000_000)
    assert tl12.effective_thrust == pytest.approx(0.02)
    assert tl12.cost == pytest.approx(8_000_000)


def test_spinext_solar_sail_panel_mode_doubles_cost_and_generates_half_panel_output():
    sail = SpinExtSolarSailTL8(tons=10, solar_panel_mode=True)
    sail.bind(DummyOwner(8, 100))

    assert sail.cost == pytest.approx(8_000_000)
    assert sail.output == pytest.approx(10.0)
    assert sail.build_item() == 'SpinExt Solar Sail (TL 8), Thrust 0.01, Power 10'
    assert 'Acts as solar panels for double cost at half same-tonnage solar panel Power' in sail.notes.infos


def test_spinext_solar_sail_panel_mode_contributes_to_available_power():
    my_ship = ship.Ship(
        tl=8,
        displacement=100,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(solar_sail=SpinExtSolarSailTL8(tons=10, solar_panel_mode=True)),
        power=PowerSection(plant=FusionPlantTL8(output=20)),
    )

    row = my_ship.build_spec().row('SpinExt Solar Sail (TL 8), Thrust 0.01, Power 10', section='Propulsion')

    assert my_ship.available_power == pytest.approx(30.0)
    assert row.power == pytest.approx(10.0)


def test_power_section_all_parts():
    power = PowerSection(plant=FusionPlantTL12(output=8))
    assert power._all_parts() == [power.plant]


def test_mdrive_tl_too_low():
    d = MDrive6()
    d.bind(DummyOwner(11, 6))
    assert 'Requires TL12, ship is TL11' in d.notes.errors


def test_mdrive_recomputes_cost_from_input():
    d = MDrive6.model_validate({'cost': 999})
    d.bind(DummyOwner(12, 6))
    assert d.cost == pytest.approx(720_000)


def test_mdrive_recomputes_tons_from_input():
    d = MDrive6.model_validate({'tons': 999})
    d.bind(DummyOwner(12, 6))
    assert d.tons == pytest.approx(0.36)


def test_mdrive_values_are_computed_properties_not_serialized_fields():
    d = MDrive6.model_validate({'tons': 999, 'cost': 999, 'power': 999})
    d.bind(DummyOwner(12, 6))
    assert d.tons == pytest.approx(0.36)
    assert d.cost == pytest.approx(720_000)
    assert d.power == pytest.approx(4.0)
    dump = d.model_dump()
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


# --- FusionPlant ---


def test_fusion_plant_base_tons():
    p = FusionPlantTL12(output=8)
    p.bind(DummyOwner(12, 6))
    assert p.tl == 12
    assert p.assembly_tl == 12
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


def test_fusion_plant_values_are_computed_properties_not_serialized_fields():
    p = FusionPlantTL12.model_validate({'output': 8, 'tons': 999, 'cost': 999, 'power': 999})
    p.bind(DummyOwner(12, 6))
    assert p.tons == pytest.approx(8 / 15)
    assert p.cost == pytest.approx(8 / 15 * 1_000_000)
    assert p.power == pytest.approx(0.0)
    dump = p.model_dump()
    assert dump['output'] == 8
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


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
    p = FusionPlantTL12(output=482, customisation=Budget(modifications=[IncreasedSize]))
    p.bind(DummyOwner(13, 400))
    assert p.build_item() == 'Fusion (TL 12), Power 482'
    assert float(p.tons) == pytest.approx(40.1666666667)
    assert float(p.cost) == pytest.approx(24_100_000.0)


def test_size_reduced_fusion_plant_values():
    p = FusionPlantTL12(output=436, customisation=Advanced(modifications=[SizeReduction]))
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
            plant=FusionPlantTL12(output=436, customisation=Advanced(modifications=[SizeReduction])),
            emergency_power_system=EmergencyPowerSystem.from_fusion_plant(
                FusionPlantTL12(output=436, customisation=Advanced(modifications=[SizeReduction]))
            ),
        ),
    )
    assert my_ship.power is not None
    eps = my_ship.power.emergency_power_system
    assert eps is not None
    assert eps.tons == pytest.approx(2.616)
    assert eps.cost == pytest.approx(3_197_333.3333)


def test_emergency_power_system_values_are_computed_properties_not_serialized_fields():
    my_ship = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        power=PowerSection(
            plant=FusionPlantTL12(output=436, customisation=Advanced(modifications=[SizeReduction])),
            emergency_power_system=EmergencyPowerSystem.model_validate({'tons': 999, 'cost': 999, 'power': 999}),
        ),
    )
    assert my_ship.power is not None
    eps = my_ship.power.emergency_power_system
    assert eps is not None
    assert eps.tons == pytest.approx(2.616)
    assert eps.cost == pytest.approx(3_197_333.3333)
    assert eps.power == pytest.approx(0.0)
    dump = eps.model_dump()
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_fusion_plant_rejects_ship_below_tl():
    plant = FusionPlantTL12(output=8)
    plant.bind(DummyOwner(11, 6))
    assert 'Requires TL12, ship is TL11' in plant.notes.errors


def _make_ship_with_plant():
    fuel = OperationFuel(weeks=1)
    s = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.streamlined_hull),
        power=PowerSection(plant=FusionPlantTL12(output=8)),
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
    assert 'Ship must have a power plant to compute OperationFuel' in my_ship.fuel.operation_fuel.notes.errors


def test_rdrive_tons_cost_and_power():
    d = RDrive16()
    d.bind(DummyOwner(12, 6))
    assert d.tl == 12
    assert d.bulkhead_label() == 'R-Drive'
    assert d.tons == pytest.approx(1.92)
    assert d.cost == pytest.approx(384_000)
    assert d.power == 0.0


def test_rdrive_values_are_computed_properties_not_serialized_fields():
    d = RDrive16.model_validate({'tons': 999, 'cost': 999, 'power': 999})
    d.bind(DummyOwner(12, 6))
    assert d.tons == pytest.approx(1.92)
    assert d.cost == pytest.approx(384_000)
    assert d.power == pytest.approx(0.0)
    dump = d.model_dump()
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_rdrive_unsupported_level_errors():
    with pytest.raises(ValueError, match='rdrive_99'):
        TypeAdapter(RDrive).validate_python({'drive_type': 'rdrive_99'})


def test_rdrive_tl_too_low():
    d = RDrive16()
    d.bind(DummyOwner(11, 6))
    assert 'Requires TL12, ship is TL11' in d.notes.errors


def test_reaction_fuel_minutes_of_operation():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(r_drive=RDrive16()),
        fuel=FuelSection(reaction_fuel=ReactionFuel(minutes=52)),
    )
    assert my_ship.fuel is not None
    assert my_ship.fuel.reaction_fuel is not None
    assert my_ship.fuel.reaction_fuel.tons == pytest.approx(2.08)


def test_reaction_fuel_respects_fuel_efficient_rdrive_customisation():
    my_ship = ship.Ship(
        tl=13,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(r_drive=RDrive16(customisation=Advanced(modifications=[FuelEfficient]))),
        fuel=FuelSection(reaction_fuel=ReactionFuel(minutes=52)),
    )

    assert my_ship.fuel is not None
    assert my_ship.fuel.reaction_fuel is not None
    assert my_ship.fuel.reaction_fuel.tons == pytest.approx(2.08 * 0.8)
    assert my_ship.drives is not None
    r_drive = my_ship.drives.r_drive
    assert r_drive is not None
    assert 'Modification not allowed for RDrive16: Fuel Efficient' not in r_drive.notes.errors
    assert 'Advanced: Fuel Efficient' in r_drive.notes.infos


def test_reaction_fuel_respects_fuel_inefficient_rdrive_customisation():
    my_ship = ship.Ship(
        tl=12,
        displacement=6,
        hull=hull.Hull(configuration=hull.standard_hull),
        drives=DriveSection(r_drive=RDrive16(customisation=Budget(modifications=[FuelInefficient]))),
        fuel=FuelSection(reaction_fuel=ReactionFuel(minutes=52)),
    )

    assert my_ship.fuel is not None
    assert my_ship.fuel.reaction_fuel is not None
    assert my_ship.fuel.reaction_fuel.tons == pytest.approx(2.08 * 1.25)
    assert my_ship.drives is not None
    r_drive = my_ship.drives.r_drive
    assert r_drive is not None
    assert 'Modification not allowed for RDrive16: Fuel Inefficient' not in r_drive.notes.errors
    assert 'Budget: Fuel Inefficient' in r_drive.notes.infos


def test_customised_rdrive_roundtrips():
    original = RDrive16(customisation=Budget(modifications=[FuelInefficient]))
    restored = TypeAdapter(RDrive).validate_json(original.model_dump_json())

    assert isinstance(restored, RDrive16)
    assert restored.customisation is not None
    assert restored.customisation.modifications == [FuelInefficient]


def test_size_reduced_fusion_plant_item_includes_output_but_not_customisation_label():
    p = FusionPlantTL12(output=436, customisation=Advanced(modifications=[SizeReduction]))
    p.bind(DummyOwner(13, 400))
    assert p.build_item() == 'Fusion (TL 12), Power 436'


def test_size_reduced_fusion_plant_has_customisation_note():
    p = FusionPlantTL12(output=436, customisation=Advanced(modifications=[SizeReduction]))
    p.bind(DummyOwner(13, 400))
    info_notes = p.notes.infos
    assert 'Advanced: Size Reduction' in info_notes


def test_budget_increased_size_mdrive_item_is_base_name_only():
    p = MDrive1(customisation=Budget(modifications=[IncreasedSize]))
    p.bind(DummyOwner(12, 100))
    assert p.build_item() == 'M-Drive 1'


def test_budget_increased_size_mdrive_has_customisation_note():
    p = MDrive1(customisation=Budget(modifications=[IncreasedSize]))
    p.bind(DummyOwner(12, 100))
    info_notes = p.notes.infos
    assert 'Budget: Increased Size' in info_notes


def test_mdrive_unsupported_level_errors():
    with pytest.raises(ValueError, match='mdrive_99'):
        TypeAdapter(MDrive).validate_python({'drive_type': 'mdrive_99'})


def test_jdrive_build_item_parsecs_and_bulkhead_label():
    d = JDrive2()
    d.bind(DummyOwner(11, 200))
    assert d.build_item() == 'Jump 2'
    assert d.parsecs == 2
    assert d.bulkhead_label() == 'Jump Drive'


def test_jdrive_unsupported_level_errors():
    with pytest.raises(ValueError, match='jdrive_99'):
        TypeAdapter(JDrive).validate_python({'drive_type': 'jdrive_99'})


def test_jdrive_tl_too_low():
    d = JDrive2()
    d.bind(DummyOwner(10, 200))
    assert 'Requires TL11, ship is TL10' in d.notes.errors


def test_emergency_power_system_requires_fusion_plant():
    with pytest.raises(RuntimeError, match='EmergencyPowerSystem requires a power plant'):
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
            plant=FusionPlantTL12(output=436, customisation=Advanced(modifications=[SizeReduction])),
            emergency_power_system=EmergencyPowerSystem(),
        ),
    )
    spec = my_ship.build_spec()
    row = spec.row('Emergency Power System', section='Power')
    assert row.tons == pytest.approx(2.616)
    assert row.cost == pytest.approx(3_197_333.3333)

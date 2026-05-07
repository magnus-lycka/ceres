import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.sensors import (
    AdvancedSensors,
    BasicSensors,
    CivilianSensors,
    CountermeasuresSuite,
    EnhancedSignalProcessing,
    ExtendedArrays,
    ImprovedSensors,
    LifeScannerAnalysisSuite,
    MilitarySensors,
    RapidDeploymentExtendedArrays,
    SensorsSection,
    SensorStations,
)


class DummyOwner(ShipBase):
    def __init__(self, tl, displacement):
        super().__init__(tl=tl, displacement=displacement)


def test_basic_sensors_have_zero_tons_cost_and_power():
    s = BasicSensors()
    s.bind(DummyOwner(12, 100))
    assert s.tons == 0
    assert s.cost == 0
    assert s.power == 0


def test_basic_sensors_notes_describe_suite_and_dm():
    s = BasicSensors()
    s.bind(DummyOwner(12, 100))
    notes = s.notes
    assert notes.items == ['Basic Sensors']
    assert notes.contents == ['Passive optical and thermal sensors, Radar, Lidar']
    assert notes.infos == ['DM -4 to Electronics (comms) and Electronics (sensors) checks']


def test_civilian_grade_tons():
    s = CivilianSensors()
    s.bind(DummyOwner(12, 6))
    assert s.tl == 9
    assert s.assembly_tl == 12
    assert float(s.tons) == 1.0


def test_civilian_grade_cost():
    s = CivilianSensors()
    s.bind(DummyOwner(12, 6))
    assert float(s.cost) == 3_000_000


def test_civilian_grade_power():
    s = CivilianSensors()
    s.bind(DummyOwner(12, 6))
    assert s.power == 1


def test_civilian_grade_notes_describe_suite_and_dm():
    s = CivilianSensors()
    s.bind(DummyOwner(12, 6))
    notes = s.notes
    assert notes.items == ['Civilian Grade Sensors']
    assert notes.contents == ['Passive optical and thermal sensors, Radar, Lidar']
    assert notes.infos == ['DM -2 to Electronics (comms) and Electronics (sensors) checks']


def test_military_grade_notes_describe_suite_and_dm():
    s = MilitarySensors()
    s.bind(DummyOwner(12, 100))
    notes = s.notes
    assert notes.items == ['Military Grade Sensors']
    assert notes.contents == ['Passive optical and thermal sensors, Radar, Lidar, Jammers, EMCON']
    assert notes.infos == ['DM +0 to Electronics (comms) and Electronics (sensors) checks']


def test_improved_sensors_at_tl13_include_expected_features():
    s = ImprovedSensors()
    s.bind(DummyOwner(13, 100))
    notes = s.notes
    assert notes.items == ['Improved Sensors']
    assert notes.contents == ['Passive optical and thermal sensors, Radar, Lidar, Densitometer, Jammers, EMCON']
    assert notes.infos == ['DM +1 to Electronics (comms) and Electronics (sensors) checks']


def test_basic_sensors_at_tl8_have_no_lpi_or_elpi():
    s = BasicSensors()
    s.bind(DummyOwner(8, 100))
    assert 'Passive optical and thermal sensors, Radar, Lidar' in s.notes.contents


def test_improved_sensors_at_tl12_do_not_upgrade_densitometer_by_default():
    s = ImprovedSensors()
    s.bind(DummyOwner(12, 100))
    assert 'Passive optical and thermal sensors, Radar, Lidar, Densitometer, Jammers, EMCON' in s.notes.contents


def test_advanced_sensors_include_neural_activity_sensor_and_extreme_emissions_control():
    s = AdvancedSensors()
    s.bind(DummyOwner(15, 100))
    notes = s.notes
    assert notes.items == ['Advanced Sensors']
    assert notes.contents == [
        'Passive optical and thermal sensors, Radar, Lidar, '
        'Densitometer, Neural Activity Sensor (passive only), Jammers, '
        'Extreme Emissions Control'
    ]
    assert notes.infos == ['DM +2 to Electronics (comms) and Electronics (sensors) checks']


def test_basic_sensors_lpi_double_cost_and_note():
    s = BasicSensors(low_intercept='LPI')
    s.bind(DummyOwner(9, 100))
    assert s.cost == 0
    notes = s.notes
    assert 'Passive optical and thermal sensors, Radar (LPI), Lidar (LPI)' in notes.contents
    assert 'DM -1 to detect the ship by sensor emissions while using low-intercept mode' in notes.infos


def test_civilian_sensors_lpi_double_cost():
    s = CivilianSensors(low_intercept='LPI')
    s.bind(DummyOwner(12, 100))
    assert s.cost == 6_000_000


def test_civilian_sensors_elpi_double_cost_and_note():
    s = CivilianSensors(low_intercept='ELPI')
    s.bind(DummyOwner(10, 100))
    assert s.cost == 6_000_000
    notes = s.notes
    assert 'Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI)' in notes.contents
    assert 'DM -3 to detect the ship by sensor emissions while using low-intercept mode' in notes.infos


def test_basic_sensors_lpi_tl_too_low():
    s = BasicSensors(low_intercept='LPI')
    s.bind(DummyOwner(8, 100))
    assert 'LPI requires TL9 for installed radar/lidar' in s.notes.errors


def test_basic_sensors_elpi_tl_too_low():
    s = BasicSensors(low_intercept='ELPI')
    s.bind(DummyOwner(9, 100))
    assert 'ELPI requires TL10 for installed radar/lidar' in s.notes.errors


def test_improved_sensors_lpi_upgrade_radar_lidar_and_densitometer_when_available():
    s = ImprovedSensors(low_intercept='LPI')
    s.bind(DummyOwner(13, 100))
    assert (
        'Passive optical and thermal sensors, Radar (LPI), Lidar (LPI), Densitometer (LPI), Jammers, EMCON'
        in s.notes.contents
    )


def test_improved_sensors_elpi_omits_densitometer_when_unavailable():
    s = ImprovedSensors(low_intercept='ELPI')
    s.bind(DummyOwner(13, 100))
    assert 'Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI), Jammers, EMCON' in s.notes.contents
    assert 'Densitometer is unavailable in ELPI mode at TL13' in s.notes.infos


def test_advanced_sensors_elpi_includes_densitometer_but_not_neural_activity_sensor():
    s = AdvancedSensors(low_intercept='ELPI')
    s.bind(DummyOwner(15, 100))
    assert (
        'Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI), '
        'Densitometer (ELPI), Jammers, Extreme Emissions Control'
    ) in s.notes.contents
    assert 'Neural Activity Sensor is unavailable in ELPI mode' in s.notes.infos


def test_civilian_grade_recomputes_tons_from_input():
    s = CivilianSensors.model_validate({'tons': 999})
    s.bind(DummyOwner(12, 6))
    assert s.tons == 1


def test_civilian_grade_recomputes_cost_from_input():
    s = CivilianSensors.model_validate({'cost': 999})
    s.bind(DummyOwner(12, 6))
    assert s.cost == 3_000_000


@pytest.mark.parametrize(
    ('part', 'expected_tons', 'expected_cost', 'expected_power'),
    [
        (BasicSensors(), 0.0, 0.0, 0.0),
        (CivilianSensors(), 1.0, 3_000_000.0, 1.0),
        (CivilianSensors(low_intercept='LPI'), 1.0, 6_000_000.0, 1.0),
        (MilitarySensors(), 2.0, 4_100_000.0, 2.0),
        (ImprovedSensors(), 3.0, 4_300_000.0, 3.0),
        (AdvancedSensors(), 5.0, 5_300_000.0, 6.0),
        (CountermeasuresSuite(), 2.0, 4_000_000.0, 1.0),
        (LifeScannerAnalysisSuite(), 1.0, 4_000_000.0, 1.0),
        (EnhancedSignalProcessing(), 2.0, 8_000_000.0, 2.0),
        (SensorStations(count=2), 2.0, 1_000_000.0, 0.0),
    ],
)
def test_sensor_values_are_computed_properties_not_serialized_fields(
    part, expected_tons, expected_cost, expected_power
):
    part.bind(DummyOwner(15, 400))
    dump = part.model_dump()

    assert part.tons == pytest.approx(expected_tons)
    assert part.cost == pytest.approx(expected_cost)
    assert part.power == pytest.approx(expected_power)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_civilian_grade_tl_too_low():
    s = CivilianSensors()
    s.bind(DummyOwner(8, 100))
    assert 'Requires TL9, ship is TL8' in s.notes.errors


def test_sensor_stations_scale_with_count():
    s = SensorStations(count=2)
    s.bind(DummyOwner(12, 400))
    assert s.tons == 2
    assert s.cost == 1_000_000
    assert s.power == 0


def test_sensor_stations_can_generate_armoured_bulkhead():
    s = SensorStations(count=2, armoured_bulkhead=True)
    s.bind(DummyOwner(12, 400))
    assert s.build_item() == 'Sensor Stations'
    assert s.tons == 2.0
    assert s.cost == 1_000_000
    assert s.armoured_bulkhead_part is not None
    assert s.armoured_bulkhead_part.tons == pytest.approx(0.2)
    assert s.armoured_bulkhead_part.cost == pytest.approx(40_000)


def test_enhanced_signal_processing_values():
    s = EnhancedSignalProcessing()
    s.bind(DummyOwner(13, 400))
    assert s.tons == 2
    assert s.cost == 8_000_000
    assert s.power == 2
    assert 'DM +4 to all sensor-related checks' in s.notes.infos


def test_countermeasures_suite_notes_explain_bonus():
    from ceres.make.ship.sensors import CountermeasuresSuite

    s = CountermeasuresSuite()
    s.bind(DummyOwner(13, 400))
    assert 'DM +4 to all jamming and electronic warfare attempts' in s.notes.infos


def test_life_scanner_analysis_suite_notes_explain_capability():
    from ceres.make.ship.sensors import LifeScannerAnalysisSuite

    s = LifeScannerAnalysisSuite()
    s.bind(DummyOwner(14, 400))
    notes = s.notes
    assert 'Advanced ship-mounted life scanner' in notes.contents
    assert 'Requires Electronics (sensors) to interpret; improves biological analysis' in notes.infos


def test_extended_arrays_add_twice_primary_sensor_values():
    s = ExtendedArrays()
    owner = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=ImprovedSensors()),
    )
    owner.sensors.primary.bind(owner)
    s.bind(owner)
    assert s.tons == 6
    assert s.cost == 8_600_000
    assert s.power == 9


def test_extended_arrays_values_are_computed_properties_not_serialized_fields():
    s = ExtendedArrays.model_validate({'tons': 999, 'cost': 999, 'power': 999})
    owner = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=ImprovedSensors()),
    )
    owner.sensors.primary.bind(owner)
    s.bind(owner)
    dump = s.model_dump()

    assert s.tons == pytest.approx(6.0)
    assert s.cost == pytest.approx(8_600_000.0)
    assert s.power == pytest.approx(9.0)
    assert 'tons' not in dump
    assert 'cost' not in dump
    assert 'power' not in dump


def test_rapid_deployment_extended_arrays_values():
    s = RapidDeploymentExtendedArrays()
    owner = ship.Ship(
        tl=13,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=ImprovedSensors()),
    )
    owner.sensors.primary.bind(owner)
    s.bind(owner)
    assert s.build_item() == 'Rapid Deployment Extended Arrays'
    assert s.tons == 6
    assert s.cost == 17_200_000
    assert s.power == 9

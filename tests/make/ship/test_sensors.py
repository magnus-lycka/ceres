import pytest

from ceres.make.ship import hull, ship
from ceres.make.ship.base import ShipBase
from ceres.make.ship.sensors import (
    AdvancedSensors,
    BasicSensors,
    CivilianSensors,
    CountermeasuresSuite,
    DeepPenetrationScanners,
    DistributedArray,
    EnhancedSignalProcessing,
    ExtendedArrays,
    ExtensionNet,
    ImprovedSensors,
    ImprovedSignalProcessing,
    LifeScanner,
    LifeScannerAnalysisSuite,
    MailDistributionArray,
    MilitaryCountermeasuresSuite,
    MilitarySensors,
    MineralDetectionSuite,
    RapidDeploymentExtendedArrays,
    SensorsSection,
    SensorStations,
    ShallowPenetrationSuite,
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
        (MilitaryCountermeasuresSuite(), 15.0, 28_000_000.0, 2.0),
        (LifeScanner(), 1.0, 2_000_000.0, 1.0),
        (LifeScannerAnalysisSuite(), 1.0, 4_000_000.0, 1.0),
        (MailDistributionArray(tl=10), 10.0, 20_000_000.0, 0.0),
        (MailDistributionArray(tl=13), 20.0, 10_000_000.0, 0.0),
        (MineralDetectionSuite(), 1.0, 5_000_000.0, 0.0),
        (ShallowPenetrationSuite(), 10.0, 5_000_000.0, 1.0),
        (ImprovedSignalProcessing(), 1.0, 4_000_000.0, 1.0),
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


def test_countermeasures_suite_uses_hg_tl():
    s = CountermeasuresSuite()
    s.bind(DummyOwner(13, 400))
    assert s.tl == 13


def test_deep_penetration_scanners_scale_with_tons():
    s = DeepPenetrationScanners(tons=4)
    s.bind(DummyOwner(13, 400))
    assert s.build_item() == 'Deep Penetration Scanners'
    assert s.tons == 4
    assert s.cost == 4_000_000
    assert s.power == 1
    assert 'Each ton scans 20 tons of target vessel per hour at Adjacent range' in s.notes.infos


def test_life_scanner_values_and_notes():
    s = LifeScanner()
    s.bind(DummyOwner(12, 400))
    assert s.tons == 1
    assert s.cost == 2_000_000
    assert s.power == 1
    assert 'Ship-mounted life scanner; typically 70-85% accurate' in s.notes.contents
    assert 'Requires Electronics (sensors) to interpret results' in s.notes.infos


def test_mail_distribution_array_tl10_values():
    s = MailDistributionArray(tl=10)
    s.bind(DummyOwner(10, 400))
    assert s.build_item() == 'Mail Distribution Array (TL10)'
    assert s.tons == 10
    assert s.cost == 20_000_000
    assert s.power == 0


def test_mail_distribution_array_tl13_values():
    s = MailDistributionArray(tl=13)
    s.bind(DummyOwner(13, 400))
    assert s.build_item() == 'Mail Distribution Array (TL13)'
    assert s.tons == 20
    assert s.cost == 10_000_000
    assert s.power == 0


def test_mineral_detection_suite_requires_densitometer_sensor_package():
    s = MineralDetectionSuite()
    owner = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=MilitarySensors(), mineral_detection_suite=s),
    )
    s.bind(owner)
    assert 'Mineral detection suite requires a sensor package with a densitometer' in s.notes.errors


def test_mineral_detection_suite_accepts_improved_sensors():
    s = MineralDetectionSuite()
    owner = ship.Ship(
        tl=12,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=ImprovedSensors(), mineral_detection_suite=s),
    )
    s.bind(owner)
    assert not s.notes.errors


def test_shallow_penetration_suite_values_and_notes():
    s = ShallowPenetrationSuite()
    s.bind(DummyOwner(10, 400))
    assert s.tons == 10
    assert s.cost == 5_000_000
    assert s.power == 1
    assert 'Thermal/EM hull penetration scanning up to Very Long range' in s.notes.contents


def test_improved_signal_processing_values_and_notes():
    s = ImprovedSignalProcessing()
    s.bind(DummyOwner(11, 400))
    assert s.tons == 1
    assert s.cost == 4_000_000
    assert s.power == 1
    assert 'DM +2 to all sensor-related checks' in s.notes.infos
    assert 'Other ships double all jamming DMs against this ship' in s.notes.infos


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


def test_distributed_array_adds_twice_primary_sensor_values_for_large_ship():
    s = DistributedArray()
    owner = ship.Ship(
        tl=13,
        displacement=6000,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=ImprovedSensors(), distributed_array=s),
    )
    owner.sensors.primary.bind(owner)
    s.bind(owner)
    assert s.tons == 6
    assert s.cost == 8_600_000
    assert s.power == 9
    assert 'Extends EM and active radar/lidar detection to Distant range' in s.notes.infos


def test_distributed_array_requires_improved_or_advanced_sensors():
    s = DistributedArray()
    owner = ship.Ship(
        tl=13,
        displacement=6000,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=MilitarySensors(), distributed_array=s),
    )
    s.bind(owner)
    assert 'Distributed array requires Improved or Advanced sensors' in s.notes.errors


def test_distributed_array_requires_large_ship():
    s = DistributedArray()
    owner = ship.Ship(
        tl=13,
        displacement=5000,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=ImprovedSensors(), distributed_array=s),
    )
    s.bind(owner)
    assert 'Distributed array requires displacement greater than 5000 tons' in s.notes.errors


def test_extension_net_values_scale_with_ship_size():
    s = ExtensionNet()
    owner = ship.Ship(
        tl=10,
        displacement=400,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=MilitarySensors(), extension_net=s),
    )
    s.bind(owner)
    assert s.tons == 4
    assert s.cost == 4_000_000
    assert s.power == 0
    assert 'Raises Limited or Full detail range by one step' in s.notes.infos


def test_extension_net_has_one_ton_minimum():
    s = ExtensionNet()
    owner = ship.Ship(
        tl=10,
        displacement=50,
        hull=hull.Hull(configuration=hull.standard_hull),
        sensors=SensorsSection(primary=BasicSensors(), extension_net=s),
    )
    s.bind(owner)
    assert s.tons == 1
    assert s.cost == 1_000_000


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

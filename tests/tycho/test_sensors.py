import pytest

from tycho import hull, ship
from tycho.base import ShipBase
from tycho.sensors import (
    AdvancedSensors,
    BasicSensors,
    CivilianSensors,
    EnhancedSignalProcessing,
    ExtendedArrays,
    ImprovedSensors,
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
    assert [(note.category.value, note.message) for note in s.notes] == [
        ('item', 'Basic Sensors'),
        ('info', 'Features: Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI)'),
        ('info', 'DM -4 to Electronics (comms) and Electronics (sensors) checks'),
    ]


def test_civilian_grade_tons():
    s = CivilianSensors()
    s.bind(DummyOwner(12, 6))
    assert s.minimum_tl == 9
    assert s.ship_tl == 12
    assert s.effective_tl == 12
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
    assert [(note.category.value, note.message) for note in s.notes] == [
        ('item', 'Civilian Grade Sensors'),
        ('info', 'Features: Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI)'),
        ('info', 'DM -2 to Electronics (comms) and Electronics (sensors) checks'),
    ]


def test_military_grade_notes_describe_suite_and_dm():
    s = MilitarySensors()
    s.bind(DummyOwner(12, 100))
    assert [(note.category.value, note.message) for note in s.notes] == [
        ('item', 'Military Grade Sensors'),
        (
            'info',
            'Features: Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI), '
            'Jammers, EMCON',
        ),
        ('info', 'DM +0 to Electronics (comms) and Electronics (sensors) checks'),
    ]


def test_improved_sensors_at_tl13_include_expected_features():
    s = ImprovedSensors()
    s.bind(DummyOwner(13, 100))
    assert [(note.category.value, note.message) for note in s.notes] == [
        ('item', 'Improved Sensors'),
        (
            'info',
            'Features: Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI), '
            'Densitometer (LPI), Jammers, EMCON',
        ),
        ('info', 'DM +1 to Electronics (comms) and Electronics (sensors) checks'),
    ]


def test_basic_sensors_at_tl8_have_no_lpi_or_elpi():
    s = BasicSensors()
    s.bind(DummyOwner(8, 100))
    assert ('info', 'Features: Passive optical and thermal sensors, Radar, Lidar') in [
        (note.category.value, note.message) for note in s.notes
    ]


def test_improved_sensors_at_tl12_do_not_yet_upgrade_densitometer_to_lpi():
    s = ImprovedSensors()
    s.bind(DummyOwner(12, 100))
    assert (
        'info',
        'Features: Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI), '
        'Densitometer, Jammers, EMCON',
    ) in [(note.category.value, note.message) for note in s.notes]


def test_improved_sensors_at_tl15_upgrade_densitometer_to_elpi():
    s = ImprovedSensors()
    s.bind(DummyOwner(15, 100))
    assert (
        'info',
        'Features: Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI), '
        'Densitometer (ELPI), Jammers, EMCON',
    ) in [(note.category.value, note.message) for note in s.notes]


def test_advanced_sensors_include_neural_activity_sensor_and_extreme_emissions_control():
    s = AdvancedSensors()
    s.bind(DummyOwner(15, 100))
    assert [(note.category.value, note.message) for note in s.notes] == [
        ('item', 'Advanced Sensors'),
        (
            'info',
            'Features: Passive optical and thermal sensors, Radar (ELPI), Lidar (ELPI), '
            'Densitometer (ELPI), Neural Activity Sensor (passive only), Jammers, '
            'Extreme Emissions Control',
        ),
        ('info', 'DM +2 to Electronics (comms) and Electronics (sensors) checks'),
    ]


def test_civilian_grade_recomputes_tons_from_input():
    s = CivilianSensors.model_validate({'tons': 999})
    s.bind(DummyOwner(12, 6))
    assert s.tons == 1


def test_civilian_grade_recomputes_cost_from_input():
    s = CivilianSensors.model_validate({'cost': 999})
    s.bind(DummyOwner(12, 6))
    assert s.cost == 3_000_000


def test_civilian_grade_tl_too_low():
    s = CivilianSensors()
    s.bind(DummyOwner(8, 100))
    assert ('error', 'Requires TL9, ship is TL8') in [
        (note.category.value, note.message) for note in s.notes
    ]


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
    assert ('info', 'DM +4 to all sensor-related checks') in [
        (note.category.value, note.message) for note in s.notes
    ]


def test_countermeasures_suite_notes_explain_bonus():
    from tycho.sensors import CountermeasuresSuite

    s = CountermeasuresSuite()
    s.bind(DummyOwner(13, 400))
    assert ('info', 'DM +4 to all jamming and electronic warfare attempts') in [
        (note.category.value, note.message) for note in s.notes
    ]


def test_life_scanner_analysis_suite_notes_explain_capability():
    from tycho.sensors import LifeScannerAnalysisSuite

    s = LifeScannerAnalysisSuite()
    s.bind(DummyOwner(14, 400))
    assert ('info', 'Advanced ship-mounted life scanner') in [
        (note.category.value, note.message) for note in s.notes
    ]
    assert ('info', 'Requires Electronics (sensors) to interpret; improves biological analysis') in [
        (note.category.value, note.message) for note in s.notes
    ]


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

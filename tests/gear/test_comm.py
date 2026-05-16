import pytest

from ceres.gear.comm import (
    BugPassiveAudio,
    BugWiredAudio,
    LaserTransceiverEquipment,
    LaserTransceiverPart,
    MesonTransceiverEquipment,
    MesonTransceiverPart,
    RadioTransceiverEquipment,
    RadioTransceiverPart,
    SatelliteUplinkPart,
    TransceiverEncryptionPart,
    TransceiverEquipment,
)
from ceres.gear.computer import ComputerPart


@pytest.mark.parametrize(
    ('equipment_cls', 'range_km', 'expected_tl'),
    [
        (RadioTransceiverEquipment, 5, 5),
        (LaserTransceiverEquipment, 500, 9),
        (MesonTransceiverEquipment, 50_000, 12),
    ],
)
def test_transceiver_resolver_defaults_to_lowest_supported_tl(equipment_cls, range_km, expected_tl):
    assert equipment_cls._resolve_spec_tl(range_km, None) == expected_tl


@pytest.mark.parametrize(
    ('equipment_cls', 'range_km', 'tl'),
    [
        (RadioTransceiverEquipment, 500_000, 12),
        (LaserTransceiverEquipment, 500, 13),
        (MesonTransceiverEquipment, 500_000, 14),
    ],
)
def test_transceiver_resolver_accepts_supported_explicit_tl(equipment_cls, range_km, tl):
    assert equipment_cls._resolve_spec_tl(range_km, tl) == tl


@pytest.mark.parametrize(
    ('equipment_cls', 'medium', 'range_km', 'tl', 'expected_tls'),
    [
        (RadioTransceiverEquipment, 'radio', 500, 8, ('TL7', 'TL9')),
        (LaserTransceiverEquipment, 'laser', 500, 10, ('TL9', 'TL11', 'TL13')),
        (MesonTransceiverEquipment, 'meson', 50_000, 13, ('TL12', 'TL14')),
    ],
)
def test_transceiver_resolver_rejects_unsupported_explicit_tl(equipment_cls, medium, range_km, tl, expected_tls):
    with pytest.raises(ValueError) as exc_info:
        equipment_cls._resolve_spec_tl(range_km, tl)

    message = str(exc_info.value)
    assert f'Unsupported {medium} transceiver' in message
    assert f'at TL{tl}' in message
    for expected_tl in expected_tls:
        assert expected_tl in message


@pytest.mark.parametrize(
    ('equipment_cls', 'medium'),
    [
        (RadioTransceiverEquipment, 'radio'),
        (LaserTransceiverEquipment, 'laser'),
        (MesonTransceiverEquipment, 'meson'),
    ],
)
def test_transceiver_resolver_rejects_unsupported_range_without_tl(equipment_cls, medium):
    with pytest.raises(ValueError) as exc_info:
        equipment_cls._resolve_spec_tl(42, None)

    assert f'Unsupported {medium} transceiver range 42km' in str(exc_info.value)


@pytest.mark.parametrize(
    ('equipment_cls', 'medium'),
    [
        (RadioTransceiverEquipment, 'radio'),
        (LaserTransceiverEquipment, 'laser'),
        (MesonTransceiverEquipment, 'meson'),
    ],
)
def test_transceiver_resolver_rejects_unsupported_range_with_tl(equipment_cls, medium):
    with pytest.raises(ValueError) as exc_info:
        equipment_cls._resolve_spec_tl(42, 12)

    assert f'Unsupported {medium} transceiver range 42km' in str(exc_info.value)


def test_wired_audio_bug():
    b = BugWiredAudio()
    assert b.tl == 5
    assert b.cost == 50
    assert b.mass_kg == 3
    item = b.build_item()
    assert item is not None and 'Wired Audio Bug' in item


def test_recording_audio_bug():
    b = BugPassiveAudio()
    assert b.tl == 6
    assert b.cost == 50
    assert b.mass_kg == 1
    item = b.build_item()
    assert item is not None and 'Recording Audio Bug' in item


def test_intro_radio_transceiver_matches_csc_values():
    transceiver = RadioTransceiverEquipment(range_km=5)

    assert transceiver.tl == 5
    assert transceiver.cost == 225.0
    assert transceiver.mass_kg == 20.0
    assert transceiver.build_item() == 'Radio Transceiver 5km'
    assert isinstance(transceiver, TransceiverEquipment)
    assert len(transceiver.parts) == 1
    assert isinstance(transceiver.parts[0], RadioTransceiverPart)
    assert transceiver.parts[0].cost == 225.0
    assert transceiver.parts[0].range_km == 5


def test_tl8_radio_transceiver_matches_csc_values():
    transceiver = RadioTransceiverEquipment(range_km=5, tl=8)

    assert transceiver.tl == 8
    assert transceiver.cost == 75.0
    assert transceiver.mass_kg == 0.0
    assert isinstance(transceiver.parts[0], RadioTransceiverPart)
    assert transceiver.parts[0].integrated_computer_processing is None


def test_tl12_continental_radio_transceiver_matches_csc_values():
    transceiver = RadioTransceiverEquipment(range_km=5_000, tl=12)

    assert transceiver.tl == 12
    assert transceiver.cost == 500.0
    assert transceiver.mass_kg == 0.0
    assert len(transceiver.parts) == 2
    assert isinstance(transceiver.parts[0], RadioTransceiverPart)
    assert isinstance(transceiver.parts[1], ComputerPart)
    assert transceiver.parts[1].processing == 0
    assert transceiver.parts[1].tl == 12


def test_tl11_laser_transceiver_matches_csc_values():
    transceiver = LaserTransceiverEquipment(range_km=500, tl=11)

    assert transceiver.tl == 11
    assert transceiver.cost == 1_500.0
    assert transceiver.mass_kg == 0.5
    assert transceiver.build_item() == 'Laser Transceiver 500km'
    assert isinstance(transceiver, TransceiverEquipment)
    assert len(transceiver.parts) == 2
    assert isinstance(transceiver.parts[0], LaserTransceiverPart)
    assert isinstance(transceiver.parts[1], ComputerPart)
    assert transceiver.parts[1].processing == 0
    assert transceiver.parts[1].tl == 11


def test_tl13_laser_transceiver_has_computer_one():
    transceiver = LaserTransceiverEquipment(range_km=500, tl=13)

    assert transceiver.tl == 13
    assert transceiver.cost == 500.0
    assert transceiver.mass_kg == 0.0
    assert len(transceiver.parts) == 2
    assert isinstance(transceiver.parts[1], ComputerPart)
    assert transceiver.parts[1].processing == 1


def test_tl12_meson_planetary_transceiver_matches_csc_values():
    transceiver = MesonTransceiverEquipment(range_km=50_000, tl=12)

    assert transceiver.tl == 12
    assert transceiver.cost == 50_000.0
    assert transceiver.mass_kg == 200.0
    assert transceiver.build_item() == 'Meson Transceiver 50,000km'
    assert isinstance(transceiver, TransceiverEquipment)
    assert len(transceiver.parts) == 2
    assert isinstance(transceiver.parts[0], MesonTransceiverPart)
    assert isinstance(transceiver.parts[1], ComputerPart)
    assert transceiver.parts[1].processing == 0
    assert transceiver.parts[1].tl == 12


def test_tl14_meson_interplanetary_transceiver_matches_csc_values():
    transceiver = MesonTransceiverEquipment(range_km=500_000, tl=14)

    assert transceiver.tl == 14
    assert transceiver.cost == 50_000.0
    assert transceiver.mass_kg == 200.0
    assert len(transceiver.parts) == 2
    assert isinstance(transceiver.parts[1], ComputerPart)
    assert transceiver.parts[1].processing == 1


def test_tl12_planetary_radio_transceiver_matches_csc_values():
    transceiver = RadioTransceiverEquipment(range_km=50_000, tl=12)

    assert transceiver.tl == 12
    assert transceiver.cost == 2_000.0
    assert transceiver.mass_kg == 2.0


def test_radio_transceiver_encryption_option_adds_hardware_part():
    transceiver = RadioTransceiverEquipment(range_km=500, tl=9, encryption=True)

    assert transceiver.tl == 9
    assert transceiver.cost == 4_500.0
    assert transceiver.mass_kg == 0.0
    assert len(transceiver.parts) == 2
    assert isinstance(transceiver.parts[1], TransceiverEncryptionPart)
    assert transceiver.parts[1].tl == 6
    assert transceiver.parts[1].cost == 4_000.0


def test_radio_transceiver_satellite_uplink_option_adds_part_and_cost():
    transceiver = RadioTransceiverEquipment(range_km=500, tl=7, satellite_uplink=True)

    assert transceiver.tl == 7
    assert transceiver.cost == 1_500.0
    assert transceiver.mass_kg == 20.0
    assert len(transceiver.parts) == 2
    assert isinstance(transceiver.parts[1], SatelliteUplinkPart)
    assert transceiver.parts[1].cost == 1_000.0
    assert transceiver.parts[1].mass_kg == 10.0
    assert transceiver.parts[1].range_multiplier == 100


def test_negligible_mass_radio_transceiver_satellite_uplink_has_minimum_mass():
    transceiver = RadioTransceiverEquipment(range_km=500, tl=9, satellite_uplink='standard')

    assert transceiver.cost == 1_500.0
    assert transceiver.mass_kg == 2.0
    assert isinstance(transceiver.parts[1], SatelliteUplinkPart)
    assert transceiver.parts[1].mass_kg == 2.0


def test_static_satellite_uplink_has_no_minimum_cost():
    transceiver = RadioTransceiverEquipment(range_km=500, tl=9, satellite_uplink='static')

    assert transceiver.cost == 750.0
    assert transceiver.mass_kg == 2.0
    assert isinstance(transceiver.parts[1], SatelliteUplinkPart)
    assert transceiver.parts[1].cost == 250.0
    assert transceiver.parts[1].static is True


def test_satellite_uplink_requires_500km_radio_range():
    try:
        RadioTransceiverEquipment(range_km=50, tl=8, satellite_uplink=True)
    except ValueError as exc:
        assert 'at least 500km range' in str(exc)
    else:
        raise AssertionError('Expected short-range satellite uplink to raise ValueError')


def test_satellite_uplink_rejects_laser_transceiver():
    try:
        LaserTransceiverEquipment(range_km=500, tl=11, satellite_uplink=True)
    except ValueError as exc:
        assert 'only available for radio transceivers' in str(exc)
    else:
        raise AssertionError('Expected laser satellite uplink to raise ValueError')


def test_tl9_interplanetary_radio_transceiver_matches_csc_values():
    transceiver = RadioTransceiverEquipment(range_km=500_000, tl=9)

    assert transceiver.tl == 9
    assert transceiver.cost == 30_000.0
    assert transceiver.mass_kg == 20.0
    assert transceiver.build_item() == 'Radio Transceiver 500,000km'


def test_radio_transceiver_rejects_unsupported_tl_for_range():
    try:
        RadioTransceiverEquipment(range_km=500, tl=8)
    except ValueError as exc:
        assert 'Unsupported radio transceiver 500km at TL8' in str(exc)
        assert 'TL7' in str(exc)
        assert 'TL9' in str(exc)
    else:
        raise AssertionError('Expected unsupported transceiver TL to raise ValueError')


def test_radio_transceiver_rejects_unsupported_range():
    try:
        RadioTransceiverEquipment(range_km=42)
    except ValueError as exc:
        assert 'Unsupported radio transceiver range 42km' in str(exc)
    else:
        raise AssertionError('Expected unsupported transceiver range to raise ValueError')


def test_laser_transceiver_rejects_unsupported_tl_for_range():
    try:
        LaserTransceiverEquipment(range_km=500, tl=10)
    except ValueError as exc:
        assert 'Unsupported laser transceiver 500km at TL10' in str(exc)
        assert 'TL9' in str(exc)
        assert 'TL11' in str(exc)
        assert 'TL13' in str(exc)
    else:
        raise AssertionError('Expected unsupported laser transceiver TL to raise ValueError')


def test_meson_transceiver_rejects_unsupported_tl_for_range():
    try:
        MesonTransceiverEquipment(range_km=50_000, tl=13)
    except ValueError as exc:
        assert 'Unsupported meson transceiver 50,000km at TL13' in str(exc)
        assert 'TL12' in str(exc)
        assert 'TL14' in str(exc)
    else:
        raise AssertionError('Expected unsupported meson transceiver TL to raise ValueError')

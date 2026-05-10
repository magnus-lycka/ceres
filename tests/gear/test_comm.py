from ceres.gear.comm import (
    BugPassiveAudio,
    BugWiredAudio,
)


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

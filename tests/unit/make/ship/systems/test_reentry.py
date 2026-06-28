"""Unit tests for systems/reentry.py — re-entry system capability table."""

import pytest

from ceres.make.ship.systems.reentry import (
    AssaultReEntryCapsule,
    BasicReEntryCapsule,
    HighSurvivabilityReEntryCapsule,
    ReEntryPod,
)


class TestReEntryCapsuleCapabilities:
    @pytest.mark.parametrize(
        ('cls', 'tl', 'capacity', 'protection', 'detection_dm', 'attack_dm'),
        [
            (BasicReEntryCapsule, 8, 1, None, None, None),
            (AssaultReEntryCapsule, 10, 1, 20, -2, None),
            (HighSurvivabilityReEntryCapsule, 14, 1, 30, -4, -2),
            (ReEntryPod, 9, 2, None, None, None),
        ],
    )
    def test_capabilities(self, cls, tl, capacity, protection, detection_dm, attack_dm):
        part = cls()
        assert part.tl == tl
        assert part.capacity == capacity
        assert part.protection == protection
        assert part.detection_dm == detection_dm
        assert part.attack_dm == attack_dm

    def test_high_survivability_notes(self):
        capsule = HighSurvivabilityReEntryCapsule()
        assert 'Protection +30' in capsule.notes.infos
        assert 'DM-4 to detect' in capsule.notes.infos
        assert 'DM-2 against attacks' in capsule.notes.infos

    def test_re_entry_pod_carries_two(self):
        pod = ReEntryPod()
        assert pod.capacity == 2
        assert 'two people' in pod.notes.infos[0]

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
        ('cls', 'tl', 'capacity', 'protection', 'detection_dm', 'attack_dm', 'tons', 'cost'),
        [
            (BasicReEntryCapsule, 8, 1, None, None, None, 0.5, 20_000.0),
            (AssaultReEntryCapsule, 10, 1, 20, -2, None, 0.5, 50_000.0),
            (HighSurvivabilityReEntryCapsule, 14, 1, 30, -4, -2, 0.5, 100_000.0),
            (ReEntryPod, 9, 2, None, None, None, 1.0, 150_000.0),
        ],
    )
    def test_capabilities(self, cls, tl, capacity, protection, detection_dm, attack_dm, tons, cost):
        part = cls()
        assert part.tl == tl
        assert part.capacity == capacity
        assert part.protection == protection
        assert part.detection_dm == detection_dm
        assert part.attack_dm == attack_dm
        assert part.tons == tons
        assert part.cost == cost
        assert part.power == 0.0

    def test_high_survivability_notes(self):
        capsule = HighSurvivabilityReEntryCapsule()
        assert 'Protection +30' in capsule.notes.infos
        assert 'DM-4 to detect' in capsule.notes.infos
        assert 'DM-2 against attacks' in capsule.notes.infos

    def test_re_entry_pod_carries_two(self):
        pod = ReEntryPod()
        assert pod.capacity == 2
        assert 'two people' in pod.notes.infos[0]

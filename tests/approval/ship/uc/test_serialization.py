"""Approval snapshots for Ship JSON serialization.

Design inputs (hull, drives, weapons, crew, software, etc.) must survive a round-trip.
Derived values (costs, power, hull_points) must NOT appear in the serialised JSON —
their absence is captured by the snapshot; their values are tracked via annotations.
Round-trip idempotency (double round-trip == identical JSON) is verified via annotation.
"""

import json

import pytest

from ceres.make.ship.ship import Ship
from tests.approval.ship.e2e.test_dragon import build_dragon
from tests.approval.ship.e2e.test_ultralight_fighter import build_ultralight_fighter
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot


def _roundtrip_json(ship: Ship) -> str:
    return Ship.model_validate_json(ship.model_dump_json()).model_dump_json()


@pytest.mark.approval
def test_ultralight_fighter_serialization(snapshot):
    """Ultralight fighter — 6-ton light hull with MDrive6, Crystaliron armour, HighTechnology laser."""
    ship = build_ultralight_fighter()
    j1 = _roundtrip_json(ship)
    snap = AnnotatedSnapshot(json.loads(ship.model_dump_json()))
    snap.annotate('production_cost', str(round(ship.production_cost, 6)))
    snap.annotate('hull_points', str(ship.hull_points))
    snap.annotate(
        'round_trip_idempotent', str(json.loads(j1) == json.loads(_roundtrip_json(Ship.model_validate_json(j1))))
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)


@pytest.mark.approval
def test_dragon_serialization(snapshot):
    """Dragon far trader — 200-ton ship with SpinExt plasma drive, weapons, crew, and software."""
    ship = build_dragon()
    j1 = _roundtrip_json(ship)
    snap = AnnotatedSnapshot(json.loads(ship.model_dump_json()))
    snap.annotate('production_cost', str(round(ship.production_cost, 6)))
    snap.annotate('hull_points', str(ship.hull_points))
    snap.annotate(
        'round_trip_idempotent', str(json.loads(j1) == json.loads(_roundtrip_json(Ship.model_validate_json(j1))))
    )
    assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

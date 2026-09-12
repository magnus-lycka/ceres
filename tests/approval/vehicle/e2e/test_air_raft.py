"""The Air/Raft, as published in the Vehicle Handbook catalogue.

Source: refs/vehicle/26_wehicle_catalogue.md — Air/Raft
"""

from types import SimpleNamespace

import pytest

from ceres.make.vehicle.armour import Face
from ceres.make.vehicle.customisations import FuelEfficiency
from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.options import (
    Autopilot,
    CollisionProtection,
    ControlSystem,
    EntertainmentSystem,
    NavigationSystem,
    SensorSystem,
    VehicleComputer,
    VehicleTransceiver,
)
from ceres.make.vehicle.speed import SpeedBand
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle
from tests.approval.snapshot import AnnotatedJSONSnapshotExtension, AnnotatedSnapshot

# Transcribed from the published stat block.
_expected = SimpleNamespace(
    tl=8,
    skill='Flyer (grav)',
    agility=1,
    speed=SpeedBand.HIGH,
    cruise_speed=SpeedBand.MEDIUM,
    range_km=2000,
    cruise_range_km=3000,
    crew=1,
    passengers=5,
    comfort_label='Basic Seating',
    cargo_tons=0.25,
    structure=2,
    shipping_tons=4,
    protection=3,
    # The published Cost is Cr250,000. It is not reproducible from the
    # construction rules: reaching the printed 2,000km range needs two steps of
    # fuel efficiency, which add half the base Cost again. The same figure
    # appears in the Core Rulebook, so it predates this design sequence and is
    # canon rather than derived — see RIV-009.
    cost=341_450,
)


def build_air_raft() -> Vehicle:
    return Vehicle(
        name='Air/Raft',
        vehicle_type=VehicleType.GRAV_VEHICLE,
        spaces=8,
        tl=8,
        crew=1,
        passengers=5,
        cargo_spaces=1,
        features=[Feature.OPEN_TOPPED],
        customisations=[FuelEfficiency(steps=2)],
        options=[
            ControlSystem(quality='basic'),
            Autopilot(quality='improved'),
            NavigationSystem(quality='basic'),
            SensorSystem(quality='basic'),
            CollisionProtection(quality='basic', spaces_protected=8),
            VehicleComputer(processing=1),
            EntertainmentSystem(),
            VehicleTransceiver(range_km=500, satellite_uplink=True),
        ],
    )


@pytest.mark.approval
class TestAirRaft:
    def test_it_matches_the_published_stat_block(self):
        air_raft = build_air_raft()

        assert air_raft.tl == _expected.tl
        assert air_raft.vehicle_type.skill == _expected.skill
        assert air_raft.agility == _expected.agility
        assert air_raft.speed is _expected.speed
        assert air_raft.cruise_speed is _expected.cruise_speed
        assert air_raft.range_km == _expected.range_km
        assert air_raft.cruise_range_km == _expected.cruise_range_km
        assert air_raft.crew == _expected.crew
        assert air_raft.passengers == _expected.passengers
        assert air_raft.comfort_label == _expected.comfort_label
        assert air_raft.cargo_tons == _expected.cargo_tons
        assert air_raft.structure == _expected.structure
        assert air_raft.shipping_tons == _expected.shipping_tons
        assert air_raft.cost == _expected.cost

    def test_every_face_carries_the_published_protection(self):
        armour = build_air_raft().armour
        assert all(armour.protection(face) == _expected.protection for face in Face)

    def test_it_is_a_legal_design(self):
        air_raft = build_air_raft()
        assert air_raft.notes.errors == []
        assert air_raft.notes.warnings == []

    def test_snapshot(self, snapshot):
        snap = AnnotatedSnapshot(build_air_raft().build_spec().model_dump(mode='json'))
        snap.annotate(
            'cost',
            'Ceres Cr341,450 vs published Cr250,000 — the published figure is canon and '
            'predates the construction rules, see RIV-009',
        )
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

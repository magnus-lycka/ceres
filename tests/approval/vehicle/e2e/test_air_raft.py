"""The Air/Raft, as published in the Vehicle Handbook catalogue.

Source: refs/vehicle/26_wehicle_catalogue.md — Air/Raft
"""

from types import SimpleNamespace

import pytest

from ceres.make.vehicle.armour import Face
from ceres.make.vehicle.customisations import FuelEfficiency
from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.grades import Grade
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
from ceres.make.vehicle.report import _build_context
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
    # The entry prints Dorsal 3 (11) like every other face. The Open-Topped
    # feature says an open-topped vehicle "has no top armour", and the other
    # open-topped catalogue designs — the Gecko, Grav Chair and Gunskiff — all
    # print Dorsal as a dash. The Air/Raft's entry is the inconsistent one — see
    # RIV-012.
    dorsal_protection=0,
    equipment=[
        'Autopilot (improved)',
        'Collision Protection (basic) x8',
        'Computer/1',
        'Control System (basic)',
        'Entertainment System',
        'Navigation System (basic)',
        'Sensor System (basic)',
        'Transceiver (improved)',
    ],
    derived_figures={
        'Autopilot (skill level)': '+1',
        'Communications (range)': '500km, satellite uplink',
        'Navigation (Navigation DM)': '+1',
        'Sensors (Electronics (sensors) DM)': '+0, 1km',
        'Camouflage (Recon DM)': '—',
        'Stealth (Electronics (sensors) DM)': '—',
    },
    # The published Cost is Cr250,000. It is not reproducible from the
    # construction rules: reaching the printed 2,000km range needs two steps of
    # fuel efficiency, which add half the base Cost again. The same figure
    # appears in the Core Rulebook, so it predates this design sequence and is
    # canon rather than derived — see RIV-009.
    cost=341_500,
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
            ControlSystem(quality=Grade.BASIC),
            Autopilot(quality=Grade.IMPROVED),
            NavigationSystem(quality=Grade.BASIC),
            SensorSystem(quality=Grade.BASIC),
            CollisionProtection(quality=Grade.BASIC, spaces_protected=8),
            VehicleComputer(processing=1),
            EntertainmentSystem(),
            VehicleTransceiver(range_km=500, stage=Grade.IMPROVED, satellite_uplink=True),
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

    def test_it_carries_the_published_equipment(self):
        assert _build_context(build_air_raft().build_spec())['equipment'] == _expected.equipment

    def test_the_equipment_confers_the_published_figures(self):
        rows = _build_context(build_air_raft().build_spec())['derived_figures']
        assert {row['label']: row['value'] for row in rows} == _expected.derived_figures

    def test_every_face_carries_the_published_protection(self):
        armour = build_air_raft().armour
        assert all(armour.protection(face) == _expected.protection for face in Face if face is not Face.DORSAL)
        assert armour.protection(Face.DORSAL) == _expected.dorsal_protection

    def test_it_is_a_legal_design(self):
        air_raft = build_air_raft()
        assert air_raft.notes.errors == []
        assert air_raft.notes.warnings == []

    def test_snapshot(self, snapshot):
        snap = AnnotatedSnapshot(build_air_raft().build_spec().model_dump(mode='json'))
        snap.annotate(
            'cost',
            'Ceres Cr341,500 vs published Cr250,000 — the published figure is canon and '
            'predates the construction rules, see RIV-009',
        )
        snap.annotate(
            'armour',
            'Ceres Dorsal 0 vs published 3 (11) — an open-topped vehicle has no top armour, as the '
            'other open-topped entries print it, see RIV-012',
        )
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

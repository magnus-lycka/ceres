"""The All Terrain Vehicle, as published in the Vehicle Handbook catalogue.

Source: refs/vehicle/26_wehicle_catalogue.md — All Terrain Vehicle (ATV)
"""

from types import SimpleNamespace

import pytest

from ceres.make.vehicle.armour import Face
from ceres.make.vehicle.customisations import AquaticDrive, FuelCapacity, FusionPlusPlant, SlowerSpeed
from ceres.make.vehicle.features import Feature
from ceres.make.vehicle.mounts import Turret
from ceres.make.vehicle.options import (
    AirLock,
    Autopilot,
    Bunk,
    CollisionProtection,
    ControlSystem,
    FireExtinguishers,
    Fresher,
    Galley,
    LifeSupport,
    NavigationSystem,
    SensorSystem,
    VacuumEnvironment,
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
    tl=12,
    agility=0,
    speed=SpeedBand.HIGH,
    cruise_speed=SpeedBand.MEDIUM,
    range_km=1250,
    # The entry prints 1,880, which is 1,250 x 1.5 rounded to the nearest ten.
    # Ceres does not round a derived figure for presentation.
    cruise_range_km=1875,
    crew=1,
    passengers=7,
    comfort_label='Extended Seating',
    cargo_tons=1.5,
    structure=4,
    shipping_tons=10,
    protection=6,
    weapons='Turret: Dorsal, can hold 4 Spaces of weapons',
    # The turret takes the last Space the design has.
    spare_spaces=0,
    # The published Cost is Cr155,000. The construction rules do not reach it:
    # vacuum environment protection and the aquatic drive, both charged per
    # vehicle Space, and the empty turret at Cr20,000 per Space it takes, come to
    # Cr90,000 between them. The same figure appears in the Core Rulebook, so it
    # predates this design sequence and is canon rather than derived — see RIV-009.
    cost=222_580,
    equipment=[
        'Air Lock',
        'Aquatic Drive (Very Slow, 600km)',
        'Autopilot (basic)',
        'Bunk x2',
        'Collision Protection (improved) x16',
        'Computer/1',
        'Control System (improved)',
        'Fire Extinguishers',
        'Fresher (standard)',
        'Fusion+ (basic) PP 2',
        'Galley (mini)',
        'Life Support (short term)',
        'Navigation System (improved)',
        'Sensor System (improved)',
        'Transceiver (superior)',
        'Vacuum Environment Protection',
    ],
)


def build_atv() -> Vehicle:
    return Vehicle(
        name='All Terrain Vehicle (ATV)',
        vehicle_type=VehicleType.GROUND_VEHICLE,
        spaces=20,
        tl=12,
        crew=1,
        passengers=7,
        cargo_spaces=6,
        features=[Feature.ATV, Feature.FAST],
        # The Slower modification is not named in the entry, because speed
        # modifications are not equipment and so never appear in an equipment
        # list. It is the only rule that produces the printed Speed of High, and
        # the two Spaces it frees are what let the ATV carry what it carries.
        customisations=[FusionPlusPlant(), FuelCapacity(spaces=-4), SlowerSpeed(), AquaticDrive()],
        mounts=[Turret(face=Face.DORSAL, weapon_spaces=4)],
        options=[
            ControlSystem(quality='improved'),
            Autopilot(quality='basic'),
            NavigationSystem(quality='improved'),
            SensorSystem(quality='improved'),
            CollisionProtection(quality='improved', spaces_protected=16),
            AirLock(),
            LifeSupport(duration='short_term', people=8),
            Bunk(count=2),
            Fresher(quality='standard'),
            Galley(quality='mini'),
            FireExtinguishers(),
            VacuumEnvironment(),
            VehicleComputer(processing=1),
            VehicleTransceiver(range_km=500, stage='superior', satellite_uplink=True, tightbeam=True, encryption=True),
        ],
    )


@pytest.mark.approval
class TestATV:
    def test_it_matches_the_published_stat_block(self):
        atv = build_atv()

        assert atv.tl == _expected.tl
        assert atv.agility == _expected.agility
        assert atv.speed is _expected.speed
        assert atv.cruise_speed is _expected.cruise_speed
        assert atv.range_km == _expected.range_km
        assert atv.cruise_range_km == _expected.cruise_range_km
        assert atv.crew == _expected.crew
        assert atv.passengers == _expected.passengers
        assert atv.comfort_label == _expected.comfort_label
        assert atv.cargo_tons == _expected.cargo_tons
        assert atv.structure == _expected.structure
        assert atv.shipping_tons == _expected.shipping_tons
        assert atv.cost == _expected.cost

    def test_it_carries_the_published_equipment(self):
        assert _build_context(build_atv().build_spec())['equipment'] == _expected.equipment

    def test_the_equipment_confers_the_published_figures(self):
        figures = {row['label']: row['value'] for row in _build_context(build_atv().build_spec())['derived_figures']}

        assert figures['Autopilot (skill level)'] == '+0'
        assert figures['Communications (range)'] == '500km, tightbeam, satellite uplink, encrypted'
        assert figures['Navigation (Navigation DM)'] == '+2'
        assert figures['Sensors (Electronics (sensors) DM)'] == '+1, 5km'

    def test_it_carries_the_published_empty_turret(self):
        # The entry's Weapons table: "Turret: Dorsal, can hold 4 Spaces of weapons",
        # every other column a dash.
        (row,) = _build_context(build_atv().build_spec())['weapons']
        assert row['weapon'] == _expected.weapons
        assert build_atv().available_spaces == _expected.spare_spaces

    def test_every_face_carries_the_published_protection(self):
        armour = build_atv().armour
        assert all(armour.protection(face) == _expected.protection for face in Face)
        # The entry prints 6 (18): Protection plus the Tech Level against small arms.
        assert armour.against_small_arms(Face.FORWARD) == _expected.protection + _expected.tl

    def test_it_is_a_legal_design(self):
        atv = build_atv()
        assert atv.notes.errors == []
        assert atv.notes.warnings == []

    def test_snapshot(self, snapshot):
        snap = AnnotatedSnapshot(build_atv().build_spec().model_dump(mode='json'))
        snap.annotate(
            'cost',
            'Ceres Cr222,580 vs published Cr155,000 — the published figure is canon and '
            'predates the construction rules, see RIV-009',
        )
        snap.annotate(
            'cruise_range_km',
            'Ceres 1,875 vs published 1,880 — the entry rounds the derived figure to the nearest ten',
        )
        assert snap == snapshot(extension_class=AnnotatedJSONSnapshotExtension)

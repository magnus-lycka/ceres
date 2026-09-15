"""Armour: Protection on each of the vehicle's six faces.

Rules: refs/vehicle/07_armour.md
"""

from ceres.make.vehicle.armour import Face
from ceres.make.vehicle.types import VehicleType
from tests.unit.make.vehicle.helpers import a_vehicle


class TestFaces:
    def test_a_vehicle_has_six_faces_in_the_order_the_catalogue_prints_them(self):
        assert list(Face) == [Face.FORWARD, Face.PORT, Face.DORSAL, Face.AFT, Face.STARBOARD, Face.VENTRAL]


class TestBaseProtection:
    """refs/vehicle/07_armour.md — Vehicle Armour. Base Protection by Tech Level,
    applied to every face unless armour is reallocated.
    """

    def test_the_published_designs(self):
        # ATV at TL12 prints 6 on every face; Air/Raft at TL8 prints 3.
        assert a_vehicle(tl=12).armour.protection(Face.FORWARD) == 6
        assert a_vehicle(tl=8, spaces=8).armour.protection(Face.DORSAL) == 3

    def test_every_face_carries_it(self):
        armour = a_vehicle(tl=12).armour
        assert all(armour.protection(face) == 6 for face in Face)

    def test_the_tech_level_bands(self):
        assert a_vehicle(tl=2).armour.protection(Face.FORWARD) == 0
        assert a_vehicle(tl=4).armour.protection(Face.FORWARD) == 1
        assert a_vehicle(tl=6).armour.protection(Face.FORWARD) == 2
        assert a_vehicle(tl=9).armour.protection(Face.FORWARD) == 3
        assert a_vehicle(tl=11).armour.protection(Face.FORWARD) == 5
        assert a_vehicle(tl=13).armour.protection(Face.FORWARD) == 6
        assert a_vehicle(tl=15).armour.protection(Face.FORWARD) == 8
        assert a_vehicle(tl=16).armour.protection(Face.FORWARD) == 10
        assert a_vehicle(tl=17).armour.protection(Face.FORWARD) == 15
        assert a_vehicle(tl=18).armour.protection(Face.FORWARD) == 20


class TestAgainstSmallArms:
    """RIV-003 — a vehicle's armour has extra Protection equal to its TL against
    attacks that are not critical, destructive or blast.
    """

    def test_it_adds_the_tech_level(self):
        # The ATV prints 6 (18) at TL12, and the Air/Raft 3 (11) at TL8.
        assert a_vehicle(tl=12).armour.against_small_arms(Face.FORWARD) == 18
        assert a_vehicle(tl=8, spaces=8).armour.against_small_arms(Face.FORWARD) == 11


class TestOpenTopped:
    """refs/vehicle/05_features.md — Open-Topped: "An open-topped vehicle has no top
    armour". refs/vehicle/07_armour.md — no face may fall below Base Protection
    "except for the dorsal face of open-topped vehicles", and the Tech Level bonus
    applies only while a face is not below it, "as in an open-topped vehicle".
    """

    def test_an_open_topped_vehicle_has_no_dorsal_protection(self):
        from ceres.make.vehicle.features import Feature

        armour = a_vehicle(vehicle_type=VehicleType.GRAV_VEHICLE, spaces=8, tl=8, features=[Feature.OPEN_TOPPED]).armour
        assert armour.protection(Face.DORSAL) == 0

    def test_its_other_faces_keep_base_protection(self):
        from ceres.make.vehicle.features import Feature

        armour = a_vehicle(vehicle_type=VehicleType.GRAV_VEHICLE, spaces=8, tl=8, features=[Feature.OPEN_TOPPED]).armour
        assert [armour.protection(face) for face in Face if face is not Face.DORSAL] == [3] * 5

    def test_the_open_top_gets_no_tech_level_bonus_against_small_arms(self):
        from ceres.make.vehicle.features import Feature

        armour = a_vehicle(vehicle_type=VehicleType.GRAV_VEHICLE, spaces=8, tl=8, features=[Feature.OPEN_TOPPED]).armour
        assert armour.against_small_arms(Face.DORSAL) == 0

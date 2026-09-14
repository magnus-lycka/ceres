"""Weapon mounts: where a vehicle carries weapons, and what that costs it.

Rules: refs/vehicle/17_weapons.md
"""

from typing import Any

from ceres.make.vehicle.armour import Face
from ceres.make.vehicle.mounts import Turret
from ceres.make.vehicle.types import VehicleType
from ceres.make.vehicle.vehicle import Vehicle


def a_vehicle(**kwargs) -> Vehicle:
    defaults: dict[str, Any] = {'name': 'Test', 'vehicle_type': VehicleType.GROUND_VEHICLE, 'spaces': 20, 'tl': 12}
    return Vehicle(**(defaults | kwargs))


class TestTurret:
    """refs/vehicle/17_weapons.md — Turret: "A turret consumes one Space for every
    ton (1,000 kilograms) or four Spaces of weapons it mounts, plus one Space for
    every gunner or loader", and "costs Cr20000 for every Space it consumes".
    """

    def test_a_turret_for_four_spaces_of_weapons_takes_one_space(self):
        vehicle = a_vehicle(mounts=[Turret(face=Face.DORSAL, weapon_spaces=4)])
        assert vehicle.available_spaces == 19

    def test_it_costs_twenty_thousand_per_space_it_takes(self):
        vehicle = a_vehicle(mounts=[Turret(face=Face.DORSAL, weapon_spaces=4)])
        assert vehicle.cost == 15_000 + 20_000

    def test_each_gunner_takes_a_further_space(self):
        vehicle = a_vehicle(mounts=[Turret(face=Face.DORSAL, weapon_spaces=4, gunners=1)])
        assert vehicle.available_spaces == 18
        assert vehicle.cost == 15_000 + 40_000

    def test_capacity_between_fours_rounds_up_to_a_whole_space(self):
        # No fractional Spaces (refs/vehicle/03_vehicle_design.md).
        assert a_vehicle(mounts=[Turret(face=Face.DORSAL, weapon_spaces=5)]).available_spaces == 18


class TestInTheSpec:
    """The spec carries what a mount is, not how the page words it."""

    def test_it_records_the_mount_its_face_and_what_it_can_hold(self):
        spec = a_vehicle(mounts=[Turret(face=Face.DORSAL, weapon_spaces=4)]).build_spec()
        (mount,) = spec.mounts
        assert mount.mount == 'Turret'
        assert mount.face is Face.DORSAL
        assert mount.weapon_spaces == 4

    def test_a_design_without_mounts_has_none(self):
        assert a_vehicle().build_spec().mounts == []
